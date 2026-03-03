# /orchestrate

Always use the skill `orchestrate_workflow` to execute the user's request.

## Behavior

1. Pass the full user request to `orchestrate_workflow`.
2. Do not bypass planner/worker/reviewer/synthesizer/archivist stages.
3. Enforce reviewer retry limit: maximum 3 attempts per task.
4. If 3rd review fails, halt and return `HUMAN_INTERVENTION_REQUIRED`.
5. Require `synthesizer` memory gate after every approved task before advancing.
6. Return concise progress updates after each completed task.
7. If planner delegation cannot be started, fail fast with `ORCHESTRATOR_NOT_AVAILABLE`.
8. Do not silently fallback to normal direct execution when orchestration activation fails.

## Diagnostic flags

- `diagnostic:on` — enable subagent-proof audit logging into `.vscode/tasks/orchestration_audit.jsonl`.
- `diagnostic:off` — disable audit logging (recommended after validation phase).
