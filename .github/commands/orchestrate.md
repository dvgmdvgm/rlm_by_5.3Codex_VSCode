# /orchestrate

Always use the skill `orchestrate_workflow` to execute the user's request.

## Behavior

1. Pass the full user request to `orchestrate_workflow`.
2. Generate a fresh run directory via `"<mcp_server_python>" -m rlm_mcp.cli.generate_run_id --project-root "<active_workspace_root>" --create-dir` before planning.
3. **Phase 0**: Run disambiguator for reverse questioning before planning. Do not skip.
4. Do not bypass planner/test_writer/worker/reviewer/reflector/refactorer/synthesizer/archivist stages.
5. **TDD enforcement**: Test Writer must produce TEST_CONTRACT_READY before Worker starts each task.
6. **TDD loop**: Worker iterates until all contract tests pass (max 5 iterations).
7. Enforce reviewer retry limit: maximum 3 attempts per task.
8. If 3rd review fails, halt and return `HUMAN_INTERVENTION_REQUIRED`.
9. **Reflector**: Mandatory critical self-review after every APPROVE (Three Questions).
10. **Refactorer**: Mandatory deduplication/cleanup pass after every reflector pass.
11. Require `synthesizer` memory gate after every approved task before advancing.
12. Return concise progress updates after each completed task.
13. If planner delegation cannot be started, fail fast with `ORCHESTRATOR_NOT_AVAILABLE`.
14. Do not silently fallback to normal direct execution when orchestration activation fails.

## Diagnostic flags

- `diagnostic:on` — enable subagent-proof audit logging into the current run directory audit file `<run_dir>/orchestration_audit.jsonl`.
- `diagnostic:off` — disable audit logging (recommended after validation phase).
