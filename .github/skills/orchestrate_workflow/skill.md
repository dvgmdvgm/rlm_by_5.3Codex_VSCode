# Skill: orchestrate_workflow

## Purpose

Run autonomous multi-step delivery using strict staged orchestration with five subagents:
- `planner`
- `worker`
- `code_reviewer`
- `synthesizer`
- `archivist`

## Trigger

Use this skill when the user asks for a large or multi-step task.

## Diagnostic mode (subagent proof)

- Toggle by request flag:
   - `diagnostic:on` enables audit logging
   - `diagnostic:off` disables audit logging
- Default: `diagnostic:on` (temporary validation mode)
- Audit file path: `.vscode/tasks/orchestration_audit.jsonl`
- Diagnostic mode MUST NOT trigger extra LLM calls by itself; it only records orchestration events.

When diagnostic mode is ON, append an audit JSON line for each stage transition with fields:
- `ts`, `run_id`, `task_id`, `agent_role`, `agent_invocation_id`, `attempt`, `event`, `status`, `notes`

## Workflow (strict state machine)

### PHASE 1 — PLANNING

1. Run `planner` with full user objective.
2. Planner must read memory first and create:
   - `.vscode/tasks/master_plan.md`
   - `.vscode/tasks/task_XX_*.md` files
3. If diagnostic mode is ON, write `planner_started` and `planner_finished` audit events.

### PHASE 2 — TASK EXECUTION LOOP

For each task from `master_plan.md` in order:

1. Set task status to `in_progress`.
2. Run `worker` on that task.
3. Run `code_reviewer`.
   - If diagnostic mode is ON, write worker/reviewer invocation events with unique `agent_invocation_id`.
4. If reviewer returns `REJECT`:
   - send reject list back to `worker`
   - retry review cycle
   - hard limit: 3 total attempts per task
5. If 3rd review is still `REJECT`:
   - HALT orchestration
   - return `HUMAN_INTERVENTION_REQUIRED` with blocker details
6. If reviewer returns `APPROVE`:
   - run `synthesizer` (mandatory memory-distribution + operational-rules gate)
   - synthesizer must evaluate ALL active operational rules for current task and execute matched actions
   - only after `MEMORY_SYNC_OK` and strict `OP_RULES_OK`, mark task `done`
   - continue to next task
   - if diagnostic mode is ON, write `synthesizer_memory_gate_ok` and `synthesizer_operational_rules_gate_ok` before advancing

### PHASE 3 — CLOSURE & CLEANUP

1. Run `archivist` to perform memory hygiene pass.
2. If and only if all tasks are `done`, all approved tasks passed `MEMORY_SYNC_OK` and `OP_RULES_OK`, and archivist returned `ARCHIVE_OK`, cleanup generated orchestration artifacts.
3. Success cleanup policy:
   - if diagnostic mode is ON and `.vscode/tasks/orchestration_audit.jsonl` exists, copy it to `memory/logs/orchestration_audit_<run_id>.jsonl`
   - run local deterministic checklist report writer (overwrite mode):
     - `python scripts/rlm/write_orchestrator_memory_checklist.py --project-root "<active_workspace_root>" --run-id "<run_id>" --status "completed"`
   - then remove `.vscode/tasks/` recursively (including generated `master_plan.md` and `task_*.md` files)
4. If workflow halts, any gate fails, or archivist does not return `ARCHIVE_OK`, do not delete `.vscode/tasks/`.
   - still run checklist writer with `--status "halted"` or `--status "failed"` to overwrite previous run report.
5. Return final condensed summary: completed tasks, halted tasks (if any), memory sync status, cleanup status.

## State management

- Keep statuses in `master_plan.md`: `todo | in_progress | review | done`.
- Ensure only one task is `in_progress` at a time.
- Record per-task attempt counters for reviewer loops.
- Persist critical outcomes to memory logs after each approved task via `synthesizer`.
- `synthesizer` must check all active operational rules from project memory for each approved task and execute only matched rules.
- `synthesizer` must re-check all active operational rules independently for each approved task (no carry-over skip/match state).
- `OP_RULES_OK` is valid only when matched rules include execution evidence (`command`, `exit_code`, `output_summary`) and no blocking-rule failures.
- Keep only one current orchestrator checklist file: `memory/logs/orchestrator_memory_checklist.md` (overwrite each run).

## RLM memory policy

- Planner and Worker must perform RLM retrieval before planning/coding.
- Reviewer must validate alignment with canonical memory.
- For large memory processing, use Sub-LM (`llm_query`/`llm_query_many`) first and pass compact results to cloud reasoning.
- Avoid cloud-side direct summarization of long memory files when Sub-LM extraction is available.
- After each approved task, memory update is mandatory through `synthesizer`.
- At workflow closure, `archivist` must verify memory hygiene and canonical consistency.

## Failure handling

- If required context is missing, issue targeted RLM query and retry once.
- If `code_reviewer` rejects the same task 3 times, stop and return a blocker report for human intervention.
- If `synthesizer` fails memory sync, stop and return `MEMORY_SYNC_BLOCKED`.
- If `synthesizer` fails operational-rules gate, stop and return `OP_RULES_BLOCKED`.
- If diagnostic mode is ON and a task halts at 3rd reject, append `HUMAN_INTERVENTION_REQUIRED` event to audit log.

## Completion criteria

Workflow is complete only when:
- all tasks are `done`
- reviewer has approved each task
- synthesizer memory gate passed for every approved task
- synthesizer operational-rules gate passed for every approved task
- archivist closure pass completed
- on successful completion, `.vscode/tasks/` generated artifacts are cleaned up
