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
- Audit file path: `<run_dir>/orchestration_audit.jsonl`
- Diagnostic mode MUST NOT trigger extra LLM calls by itself; it only records orchestration events.

When diagnostic mode is ON, append an audit JSON line for each stage transition with fields:
- `ts`, `run_id`, `task_id`, `agent_role`, `agent_invocation_id`, `attempt`, `event`, `status`, `notes`

## ⛔ CRITICAL: ANTI-BATCHING ENFORCEMENT

The following violations are FORBIDDEN and invalidate the entire run:
- **NO batch execution**: Do NOT implement multiple tasks before reviewing each one.
- **NO batch review**: Do NOT review multiple tasks in a single review pass.
- **NO skipping synthesizer**: After EVERY individual task APPROVE, you MUST run the synthesizer gate BEFORE starting the next task.
- **NO skipping archivist**: You MUST invoke archivist at closure.
- **Strict sequence per task**: Worker → Code Reviewer → Synthesizer → (next task). Breaking this order is a protocol violation.

If you find yourself about to start the next task without having produced `SYNTHESIZER_GATE_PASSED` for the previous task — **STOP. Go back and run the synthesizer.**

## ⛔ CONTEXT RESILIENCE — CHECKPOINT & RE-READ PROTOCOL

**Problem**: During long runs the conversation grows and early instructions fall out of LLM attention.
**Solution**: Externalize state to files and re-read critical instructions before every transition.

### Run directory: `.vscode/tasks/<run_id>/`

At the start of every orchestration run, generate a unique `run_id` and create a dedicated run directory by running the deterministic helper command:

```text
"<mcp_server_python>" -m rlm_mcp.cli.generate_run_id --project-root "<active_workspace_root>" --create-dir
```

Use the returned JSON values as the source of truth. Required `run_id` format:

```text
orch_YYYYMMDD_HHMMSS[_NN]
```

- `orch` — stable prefix for orchestration runs
- `YYYYMMDD_HHMMSS` — UTC timestamp to the second
- `_NN` — collision suffix added only if that timestamp directory already exists

The resulting run directory will be:

```text
.vscode/tasks/<run_id>/
```

All generated orchestration artifacts for that run MUST remain inside this directory only. Never reuse another run's directory.

### Checkpoint file: `<run_dir>/orchestrator_state.json`

After EVERY state transition (planning done, task started, task reviewed, synthesizer passed, closure started), **overwrite** this file with current state:

```json
{
  "run_id": "<run_id>",
  "phase": "planning|execution|closure",
  "current_task_index": 1,
  "total_tasks": 4,
  "tasks_completed": ["task_01"],
  "tasks_remaining": ["task_02", "task_03", "task_04"],
  "last_gate_tokens": {
    "task_01": "SYNTHESIZER_GATE_PASSED: yes"
  },
  "rules_audit_accumulated": [],
  "archivist_status": "not_started|ARCHIVE_OK|ARCHIVE_BLOCKED",
  "cleanup_done": false,
  "next_action": "start_task_02"
}
```

### Mandatory re-orientation (before EVERY new task and before closure)

Before starting each new task or entering Phase 3, you MUST:

1. **Re-read** `<run_dir>/orchestrator_state.json` to recall where you are.
2. **Re-read** `<run_dir>/master_plan.md` to recall the full plan and task statuses.
3. **Re-read** the PROTOCOL REMINDER below to refresh critical rules.
4. Only then proceed with the next action indicated by `next_action` in the checkpoint.

If you skip re-orientation and proceed from conversation memory alone — you WILL lose track. This is not optional.

### ⛔ PROTOCOL REMINDER (re-read this before every task transition)

```
CRITICAL RULES — ORCHESTRATOR PROTOCOL REMINDER
1. ONE task at a time: Worker → Reviewer → Synthesizer → next task.
2. After APPROVE: run synthesizer gate. Produce SYNTHESIZER_GATE_PASSED.
3. Do NOT start next task until SYNTHESIZER_GATE_PASSED appears.
4. After ALL tasks: run archivist. Wait for ARCHIVE_OK.
5. On success: run checklist writer, then delete `<run_dir>/` only.
6. On failure: do NOT delete `<run_dir>/`.
7. Final response MUST contain Rules Audit Report table.
8. Update orchestrator_state.json after every transition.
```

## Workflow (strict state machine)

### PHASE 1 — PLANNING

1. Run `planner` with full user objective.
2. Planner must read memory first and create:
   - `<run_dir>/master_plan.md`
   - `<run_dir>/task_XX_*.md` files
3. If diagnostic mode is ON, write `planner_started` and `planner_finished` audit events.

### PHASE 2 — TASK EXECUTION LOOP

⛔ **ONE TASK AT A TIME. COMPLETE THE FULL CYCLE (worker → reviewer → synthesizer) FOR EACH TASK BEFORE STARTING THE NEXT.**

For each task from `master_plan.md` in order:

0. **RE-ORIENT** (mandatory before every task):
   - Re-read `<run_dir>/orchestrator_state.json`
   - Re-read `<run_dir>/master_plan.md`
   - Re-read the PROTOCOL REMINDER section above
   - Confirm: which task am I about to start? What is `next_action`?

1. Set task status to `in_progress`. Update `orchestrator_state.json` with `current_task_index` and `next_action: "worker_executing"`.
2. Run `worker` on that task.
3. Run `code_reviewer`.
   - If diagnostic mode is ON, write worker/reviewer invocation events with unique `agent_invocation_id`.
4. If reviewer returns `REJECT`:
   - send reject list back to `worker`
   - retry review cycle
   - hard limit: 3 total attempts per task
5. If 3rd review is still `REJECT`:
   - HALT orchestration
   - Update `orchestrator_state.json` with `next_action: "HALTED"`
   - return `HUMAN_INTERVENTION_REQUIRED` with blocker details
6. If reviewer returns `APPROVE`:
   - Update `orchestrator_state.json` with `next_action: "synthesizer_gate"`
   - ⛔ **HARD STOP — SYNTHESIZER GATE (mandatory, cannot be skipped)**
   - Before doing ANYTHING else, you MUST execute the full synthesizer workflow:
     a. Read `memory/canonical/coding_rules.md` and `memory/canonical/active_tasks.md` to load ALL active rules.
     b. For each active rule: evaluate scope/trigger/preconditions against the current task.
     c. For matched rules: execute the action and capture evidence (command, exit_code, output_summary).
     d. For unmatched rules: record specific reason (scope mismatch, trigger not met, etc.).
     e. Persist memory updates: append facts to `memory/logs/extracted_facts.jsonl`, run `consolidate_memory`.
     f. Produce the `TASK_RULES_AUDIT` table covering ALL rules (applied/skipped/failed).
     g. Output the following gate tokens (ALL are required, absence = protocol violation):
        ```
        SYNTHESIZER_GATE for Task <ID>:
        - MEMORY_SYNC_OK: yes/no
        - RULES_CHECKED: <N>
        - RULES_MATCHED: <N>
        - RULES_EXECUTED: <N>
        - RULES_FAILED_BLOCKING: <N>
        - RULES_EVIDENCE_COMPLETE: yes/no
        - OP_RULES_OK: yes/no
        - SYNTHESIZER_GATE_PASSED: yes/no
        ```
   - Only after `SYNTHESIZER_GATE_PASSED: yes`, mark task `done` and continue to next task.
   - If `SYNTHESIZER_GATE_PASSED: no`, HALT and return blocker details.
   - If diagnostic mode is ON, write `synthesizer_memory_gate_ok` and `synthesizer_operational_rules_gate_ok` before advancing.
   - **accumulate** the synthesizer's `TASK_RULES_AUDIT` table into a run-level rules audit registry (one entry per task per rule).
   - **Update `orchestrator_state.json`**: move completed task to `tasks_completed`, update `tasks_remaining`, record `last_gate_tokens`, set `next_action` to the next task or `"closure"` if this was the last task.
   - ⛔ **You MUST NOT start the next task until SYNTHESIZER_GATE_PASSED appears in your output.**

### PHASE 3 — CLOSURE

⛔ **ARCHIVIST IS MANDATORY. Do NOT skip this phase. Do NOT go directly to final summary.**

0. **RE-ORIENT before closure** (mandatory):
   - Re-read `<run_dir>/orchestrator_state.json` — confirm all tasks are in `tasks_completed`.
   - Re-read `<run_dir>/master_plan.md` — confirm all tasks are `done`.
   - Re-read the PROTOCOL REMINDER section — refresh closure rules.
   - Update `orchestrator_state.json` with `phase: "closure"`, `next_action: "archivist"`.

1. Run `archivist` to perform memory hygiene pass (verify rules audit completeness, canonical consistency, closure gates).
2. Proceed to Phase 4 (Validation). Do NOT cleanup `<run_dir>/` yet — the validator needs `orchestrator_state.json`.

### PHASE 4 — VALIDATION

⛔ **VALIDATOR IS MANDATORY. Runs after archivist, before final cleanup.**

0. Update `orchestrator_state.json` with `phase: "validation"`, `next_action: "validator_script"`.
1. Run the deterministic validator script:
   ```
   read `.vscode/mcp.json` -> resolve `servers.rlm-memory.command` -> run `"<mcp_server_python>" -m rlm_mcp.cli.validate_orchestrator --project-root "<active_workspace_root>" --tasks-dir "<run_dir>"`
   ```
   This reads `orchestrator_state.json` + `memory/canonical/coding_rules.md` and outputs `<run_dir>/validation_report.json`.
2. Read `<run_dir>/validation_report.json`.
   - If `status == "pass"` → log `VALIDATION_PASS`, proceed to cleanup.
   - If `status == "error"` → log `VALIDATION_ERROR`, proceed to cleanup (non-blocking).
   - If `status == "fail"` → invoke `#agent:validator` to execute only the missed rules.
3. If validator agent was invoked, record its gate token (`VALIDATION_PASS` / `VALIDATION_PARTIAL` / `VALIDATION_FAIL`).
4. Update `orchestrator_state.json` with `validation_result` and `next_action: "cleanup"`.

### FINAL CLEANUP & SUMMARY

1. If all gates passed (including archivist `ARCHIVE_OK`) and no workflow halts:
   - if diagnostic mode is ON and `<run_dir>/orchestration_audit.jsonl` exists, copy it to `memory/logs/orchestration_audit_<run_id>.jsonl`
   - run local deterministic checklist report writer (overwrite mode):
     - `"<mcp_server_python>" -m rlm_mcp.cli.write_checklist --project-root "<active_workspace_root>" --tasks-dir "<run_dir>" --run-id "<run_id>" --status "completed"`
   - then remove `<run_dir>/` recursively (including generated `master_plan.md`, `task_*.md`, `orchestrator_state.json`, and `validation_report.json`)
2. If workflow halted, any gate failed, or archivist did not return `ARCHIVE_OK`, do not delete `<run_dir>/`.
   - still run checklist writer with `--status "halted"` or `--status "failed"` to overwrite previous run report.
   - `orchestrator_state.json` and `validation_report.json` remain in `<run_dir>/` for post-mortem debugging.
3. Return final condensed summary: completed tasks, halted tasks (if any), memory sync status, validation result, cleanup status.
4. **MANDATORY: Comprehensive Rules Audit Report.**
   After all tasks are processed (or workflow halts), the orchestrator MUST include in the final user-facing response a **full rules audit report** compiled from accumulated per-task `TASK_RULES_AUDIT` data:

   ```
   ## 📋 Rules Audit Report

   ### Summary
   - Total active rules in memory: <N>
   - Rules applied (at least once across all tasks): <N>
   - Rules never applied (skipped in all tasks): <N>
   - Rules failed: <N>

   ### Per-rule breakdown
   | # | rule_id / entity | rule_summary | applied_in_tasks | skipped_in_tasks | status | reason_for_skip_or_match |
   |---|------------------|--------------|------------------|------------------|--------|--------------------------|
   | 1 | <id>             | <1-line>     | Task 1, Task 3   | Task 2           | applied | scope matched: frontend CSS |
   | 2 | <id>             | <1-line>     | —                | Task 1, 2, 3     | never applied | scope: mobile deploy; no mobile tasks in run |
   ```

   - Every active rule from memory MUST appear — no omissions.
   - For rules applied in some tasks but skipped in others, show both columns.
   - For rules never applied in any task, clearly state the reason (scope mismatch, trigger not met, preconditions unsatisfied).
   - For failed rules, include error summary.
   - This report is part of the final user-facing answer — not just internal state.

## State management

- Keep statuses in `master_plan.md`: `todo | in_progress | review | done`.
- Ensure only one task is `in_progress` at a time.
- Record per-task attempt counters for reviewer loops.
- Persist critical outcomes to memory logs after each approved task via `synthesizer`.
- `synthesizer` must check all active operational rules from project memory for each approved task and execute only matched rules.
- `synthesizer` must re-check all active operational rules independently for each approved task (no carry-over skip/match state).
- `OP_RULES_OK` is valid only when matched rules include execution evidence (`command`, `exit_code`, `output_summary`) and no blocking-rule failures.
- Keep a per-run checklist snapshot: `memory/logs/orchestrator_memory_checklist_<run_id>.md`.
- Maintain a run-level **rules audit registry** that accumulates `TASK_RULES_AUDIT` from each synthesizer invocation. This registry is the source for the final Comprehensive Rules Audit Report.

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
- synthesizer memory gate passed for every approved task — verified by presence of `SYNTHESIZER_GATE_PASSED: yes` per task
- synthesizer operational-rules gate passed for every approved task
- archivist closure pass completed — verified by `ARCHIVE_OK`
- Phase 4 validation script executed — verified by presence of `validation_report.json` or `VALIDATION_PASS`/`VALIDATION_PARTIAL` token
- Comprehensive Rules Audit Report is present in the final response
- on successful completion, only the current run directory under `.vscode/tasks/<run_id>/` is cleaned up (including `validation_report.json`)

⛔ **SELF-CHECK before producing final answer**: Count how many tasks exist. Count how many `SYNTHESIZER_GATE_PASSED` tokens you produced. If they don't match — you skipped a synthesizer gate. STOP and fix it before responding.

⛔ **If your final response does not contain the Rules Audit Report table — the run is INVALID. Add it.**
