---
agent: agent
description: Run multi-step tasks through planner-worker-reviewer orchestration
---

Use skill `orchestrate_workflow` for this request.
Also apply delegation rules from `.github/prompts/orchestrator_skill.prompt.md`.

Diagnostic mode flags (put in request text):
- `diagnostic:on` -> write subagent audit events to `.vscode/tasks/orchestration_audit.jsonl`
- `diagnostic:off` -> disable audit logging

Default for now: `diagnostic:on`.

Mandatory behavior:
1. Start with planner.
2. Planner reads memory first (`reload_memory_context`, `get_memory_metadata`, canonical files).
3. Planner creates `.vscode/tasks/master_plan.md` and per-task files.
4. Write initial `.vscode/tasks/orchestrator_state.json` checkpoint after planning.
5. Fail-fast activation check: if planner delegation cannot be started immediately, return `ORCHESTRATOR_NOT_AVAILABLE` and STOP. Do not execute the user request directly.
6. **Before every new task and before closure**: re-read `orchestrator_state.json` + `master_plan.md` to re-orient (context degrades in long runs).
7. For each task: worker executes, reviewer returns APPROVE/REJECT.
8. If REJECT, send fixes back to worker and re-review (max 3 attempts).
9. If 3rd review is REJECT, halt and return `HUMAN_INTERVENTION_REQUIRED`.
10. If APPROVE, run synthesizer memory-distribution gate with operational-rules execution; continue only after `MEMORY_SYNC_OK` and strict `OP_RULES_OK` (matched rules must include command/exit-code/output evidence).
11. After synthesizer gate: update `orchestrator_state.json` checkpoint.
12. After all tasks, re-orient from checkpoint, then run archivist closure pass and cleanup.

Return concise progress updates after each completed task.
