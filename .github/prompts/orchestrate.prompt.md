---
agent: agent
description: Run multi-step tasks through planner-worker-reviewer orchestration
---

Use skill `orchestrate_workflow` for this request.
Also apply delegation rules from `.github/prompts/orchestrator_skill.prompt.md`.

Diagnostic mode flags (put in request text):
- `diagnostic:on` -> write subagent audit events to the current run directory audit file `<run_dir>/orchestration_audit.jsonl`
- `diagnostic:off` -> disable audit logging

Default for now: `diagnostic:on`.

Mandatory behavior:
1. Start with planner.
2. Planner reads memory first (`reload_memory_context`, `get_memory_metadata`, canonical files).
3. Read `.vscode/mcp.json`, resolve `servers.rlm-memory.command`, and run `"<mcp_server_python>" -m rlm_mcp.cli.generate_run_id --project-root "<active_workspace_root>" --create-dir`.
4. Use the returned JSON as the single source of truth for `run_id` and `run_dir`.
5. Require all generated artifacts for this run to stay inside that directory.
6. Planner creates `<run_dir>/master_plan.md` and per-task files.
7. Write initial `<run_dir>/orchestrator_state.json` checkpoint after planning.
8. Fail-fast activation check: if planner delegation cannot be started immediately, return `ORCHESTRATOR_NOT_AVAILABLE` and STOP. Do not execute the user request directly.
9. **Before every new task and before closure**: re-read `<run_dir>/orchestrator_state.json` + `<run_dir>/master_plan.md` to re-orient (context degrades in long runs).
10. For each task: worker executes, reviewer returns APPROVE/REJECT.
11. If REJECT, send fixes back to worker and re-review (max 3 attempts).
12. If 3rd review is REJECT, halt and return `HUMAN_INTERVENTION_REQUIRED`.
13. If APPROVE, run synthesizer memory-distribution gate with operational-rules execution; continue only after `MEMORY_SYNC_OK` and strict `OP_RULES_OK` (matched rules must include command/exit-code/output evidence).
14. After synthesizer gate: update `<run_dir>/orchestrator_state.json` checkpoint.
15. After all tasks, re-orient from checkpoint, then run archivist closure pass.
16. After archivist, read `.vscode/mcp.json`, resolve `servers.rlm-memory.command`, run `"<mcp_server_python>" -m rlm_mcp.cli.validate_orchestrator --project-root "<active_workspace_root>" --tasks-dir "<run_dir>"`, and check `<run_dir>/validation_report.json`. If missed rules found (`status == "fail"`), invoke `#agent:validator` to fix them.
17. Only after validation, run cleanup (remove `<run_dir>/` on success).

Return concise progress updates after each completed task.
