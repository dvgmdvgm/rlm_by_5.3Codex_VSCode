# /orchestrate

Always use the skill `orchestrate_workflow` to execute the user's request.

## Behavior

1. Pass the full user request to `orchestrate_workflow`.
2. Generate a fresh run directory via `"<mcp_server_python>" -m rlm_mcp.cli.generate_run_id --project-root "<active_workspace_root>" --create-dir` before planning.
3. Do not bypass planner/worker/reviewer/synthesizer/archivist stages.
4. Enforce reviewer retry limit: maximum 3 attempts per task.
5. If 3rd review fails, halt and return `HUMAN_INTERVENTION_REQUIRED`.
6. Require `synthesizer` memory gate after every approved task before advancing.
7. Return concise progress updates after each completed task.
8. If planner delegation cannot be started, fail fast with `ORCHESTRATOR_NOT_AVAILABLE`.
9. Do not silently fallback to normal direct execution when orchestration activation fails.

## Diagnostic flags

- `diagnostic:on` — enable subagent-proof audit logging into the current run directory audit file `<run_dir>/orchestration_audit.jsonl`.
- `diagnostic:off` — disable audit logging (recommended after validation phase).
