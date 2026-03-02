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
4. For each task: worker executes, reviewer returns APPROVE/REJECT.
5. If REJECT, send fixes back to worker and re-review (max 3 attempts).
6. If 3rd review is REJECT, halt and return `HUMAN_INTERVENTION_REQUIRED`.
7. If APPROVE, run synthesizer memory-distribution gate with operational-rules execution; continue only after `MEMORY_SYNC_OK` and `OP_RULES_OK`.
8. After all tasks, run archivist closure pass and cleanup.

Return concise progress updates after each completed task.
