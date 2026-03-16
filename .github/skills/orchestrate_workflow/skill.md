````skill
# Skill: orchestrate_workflow

## Purpose

Run autonomous multi-step delivery using strict staged orchestration with eight subagents:
- `disambiguator` (Phase 0 — Reverse Questioning)
- `planner` (Phase 1 — Planning)
- `test_writer` (Phase 2 — TDD Contract)
- `worker` (Phase 2 — Implementation)
- `code_reviewer` (Phase 2 — Review)
- `reflector` (Phase 2 — Critical Self-Review)
- `refactorer` (Phase 2 — Immediate Refactoring)
- `synthesizer` (Phase 2 — Memory Gate)
- `archivist` (Phase 3 — Closure)
- `validator` (Phase 4 — Validation)

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
- **NO skipping TDD**: Tests MUST be written BEFORE implementation for every task.
- **NO skipping reflector**: Critical self-review is MANDATORY after every code review approval.
- **NO skipping refactorer**: Refactoring pass is MANDATORY after every reflector pass.
- **Strict sequence per task**: Test Writer → Worker (TDD loop) → Code Reviewer → Reflector → Refactorer → Synthesizer → (next task). Breaking this order is a protocol violation.

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

After EVERY state transition (disambiguation done, planning done, tests written, task started, task reviewed, reflector done, refactorer done, synthesizer passed, closure started), **overwrite** this file with current state:

```json
{
  "run_id": "<run_id>",
  "phase": "disambiguation|planning|execution|closure|validation",
  "current_task_index": 1,
  "total_tasks": 4,
  "tasks_completed": ["task_01"],
  "tasks_remaining": ["task_02", "task_03", "task_04"],
  "current_subphase": "test_writing|implementation|tdd_loop|review|reflection|refactoring|synthesizer",
  "disambiguation_result": "DISAMBIGUATOR_PASS|DISAMBIGUATOR_BLOCKED",
  "test_contracts": {
    "task_01": "TEST_CONTRACT_READY",
    "task_02": "pending"
  },
  "tdd_loop_attempts": {
    "task_01": 2
  },
  "reflector_results": {
    "task_01": "REFLECTOR_PASS|REFLECTOR_FLAG_REFACTORING"
  },
  "refactorer_results": {
    "task_01": "REFACTORER_DONE|REFACTORER_SKIPPED"
  },
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
CRITICAL RULES — ORCHESTRATOR PROTOCOL REMINDER (v2 — Agentic Engineering)
1. ONE task at a time: Test Writer → Worker (TDD loop) → Reviewer → Reflector → Refactorer → Synthesizer → next task.
2. Test Writer must produce TEST_CONTRACT_READY before Worker starts.
3. Worker runs in TDD loop: implement → run tests → if fail → fix → run tests. Max 5 iterations.
4. After APPROVE from reviewer: run Reflector. Produce REFLECTOR_PASS or REFLECTOR_FLAG_REFACTORING.
5. After Reflector: run Refactorer. Produce REFACTORER_DONE or REFACTORER_SKIPPED.
6. After Refactorer: run Synthesizer gate. Produce SYNTHESIZER_GATE_PASSED.
7. Do NOT start next task until SYNTHESIZER_GATE_PASSED appears.
8. After ALL tasks: run Archivist. Wait for ARCHIVE_OK.
9. After Archivist: run Validator. Wait for VALIDATION_PASS.
10. On success: run checklist writer, then delete `<run_dir>/` only.
11. On failure: do NOT delete `<run_dir>/`.
12. Final response MUST contain Rules Audit Report table.
13. Update orchestrator_state.json after every transition.
```

## Workflow (strict state machine)

### PHASE 0 — DISAMBIGUATION (Reverse Questioning)

⛔ **This phase is MANDATORY. Do NOT jump straight to planning.**

1. Run `disambiguator` with the full user request and project context.
2. Disambiguator performs RLM memory lookup and analyzes the request for blind spots.
3. If disambiguator returns `DISAMBIGUATOR_PASS`:
   - Record any default assumptions in `<run_dir>/disambiguation_report.md`.
   - Proceed to Phase 1 with the refined understanding.
4. If disambiguator returns `DISAMBIGUATOR_BLOCKED`:
   - Present the disambiguator's questions to the user.
   - Wait for user answers.
   - Re-run disambiguator with answers incorporated.
   - Only proceed when `DISAMBIGUATOR_PASS` is achieved.
5. Update `orchestrator_state.json` with `phase: "disambiguation"` and result.
6. If diagnostic mode is ON, write `disambiguator_started` and `disambiguator_finished` audit events.

### PHASE 1 — PLANNING

1. Run `planner` with full user objective AND the disambiguation report.
2. Planner must read memory first and create:
   - `<run_dir>/master_plan.md` — now must include a `## Test Strategy` section per task.
   - `<run_dir>/task_XX_*.md` files — each must include `## Test Contract` section with testable criteria.
3. If diagnostic mode is ON, write `planner_started` and `planner_finished` audit events.

### PHASE 2 — TASK EXECUTION LOOP

⛔ **ONE TASK AT A TIME. COMPLETE THE FULL CYCLE (test_writer → worker TDD loop → reviewer → reflector → refactorer → synthesizer) FOR EACH TASK BEFORE STARTING THE NEXT.**

For each task from `master_plan.md` in order:

#### Step 0: RE-ORIENT (mandatory before every task)
   - Re-read `<run_dir>/orchestrator_state.json`
   - Re-read `<run_dir>/master_plan.md`
   - Re-read the PROTOCOL REMINDER section above
   - Confirm: which task am I about to start? What is `next_action`?

#### Step 1: TEST WRITER (TDD Contract)
   - Set `current_subphase: "test_writing"` in checkpoint.
   - Run `test_writer` on the current task.
   - Test Writer reads the task's acceptance criteria and writes failing tests.
   - Test Writer runs tests to confirm red phase (all new tests fail).
   - If `TEST_CONTRACT_READY`: record test file paths, proceed to Step 2.
   - If `TEST_CONTRACT_BLOCKED`: escalate to user with details. Do not proceed.
   - If diagnostic mode is ON, write `test_writer_started` and `test_writer_finished` events.

#### Step 2: WORKER + TDD LOOP (Implementation)
   - Set `current_subphase: "implementation"` in checkpoint.
   - Run `worker` on the task WITH the test contract (test file paths and expected behaviors).
   - Worker implements the feature.
   - **TDD feedback loop**:
     a. Run the Test Writer's test suite.
     b. If ALL contract tests pass → Worker is done. Set `current_subphase: "review"`. Proceed to Step 3.
     c. If ANY contract test fails → feed failure output back to Worker. Worker fixes. Repeat from (a).
     d. **Hard limit**: 5 TDD loop iterations. If tests still fail after 5 attempts:
        - HALT orchestration
        - Update checkpoint with `next_action: "HALTED_TDD_FAIL"`
        - Return `HUMAN_INTERVENTION_REQUIRED` with test failure details
   - Record `tdd_loop_attempts` count in checkpoint.
   - If diagnostic mode is ON, write `worker_started`, `tdd_loop_iteration_N`, `worker_finished` events.

#### Step 3: CODE REVIEWER (Review)
   - Run `code_reviewer` on the implemented code.
   - If diagnostic mode is ON, write reviewer invocation events with unique `agent_invocation_id`.
   - If reviewer returns `REJECT`:
     - Send reject list back to `worker`
     - Worker fixes, runs tests again (TDD loop continues)
     - Retry review cycle
     - Hard limit: 3 total review attempts per task
   - If 3rd review is still `REJECT`:
     - HALT orchestration
     - Update checkpoint with `next_action: "HALTED"`
     - Return `HUMAN_INTERVENTION_REQUIRED` with blocker details
   - If reviewer returns `APPROVE`:
     - Proceed to Step 4 (Reflector)

#### Step 4: REFLECTOR (Critical Self-Review)
   ⛔ **MANDATORY after every APPROVE. Cannot be skipped.**
   - Set `current_subphase: "reflection"` in checkpoint.
   - Run `reflector` on the approved implementation.
   - Reflector answers the Three Questions (Meaning, Simplicity, User Impact).
   - If `REFLECTOR_PASS`: proceed to Step 5 with no special flags.
   - If `REFLECTOR_FLAG_REFACTORING`: proceed to Step 5 — refactorer MUST address flagged items.
   - If `REFLECTOR_BLOCKED`: return to Worker (Step 2) for rework. This counts as a review rejection.
   - Record `reflector_results` in checkpoint.
   - If diagnostic mode is ON, write `reflector_started` and `reflector_finished` events.

#### Step 5: REFACTORER (Immediate Refactoring)
   ⛔ **MANDATORY after every Reflector pass. Cannot be skipped.**
   - Set `current_subphase: "refactoring"` in checkpoint.
   - Run `refactorer` on the task's changed files.
   - If Reflector returned `REFLECTOR_FLAG_REFACTORING`, pass the flagged items to refactorer.
   - If Reflector returned `REFLECTOR_PASS` AND task is small (<30 lines):
     - Refactorer runs in lightweight mode (duplication scan + dead code only).
   - Refactorer runs full test suite after changes to verify no regressions.
   - If `REFACTORER_DONE`: proceed to Step 6.
   - If `REFACTORER_SKIPPED`: proceed to Step 6 (no refactoring needed).
   - If `REFACTORER_BLOCKED`: proceed to Step 6 with pre-refactoring code (report issue).
   - Record `refactorer_results` in checkpoint.
   - If diagnostic mode is ON, write `refactorer_started` and `refactorer_finished` events.

#### Step 6: SYNTHESIZER GATE (Memory + Rules)
   - Set `current_subphase: "synthesizer"` in checkpoint.
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

- Keep statuses in `master_plan.md`: `todo | in_progress | test_writing | tdd_loop | review | reflection | refactoring | done`.
- Ensure only one task is `in_progress` at a time.
- Record per-task attempt counters for TDD loops and reviewer loops.
- Persist critical outcomes to memory logs after each approved task via `synthesizer`.
- `synthesizer` must check all active operational rules from project memory for each approved task and execute only matched rules.
- `synthesizer` must re-check all active operational rules independently for each approved task (no carry-over skip/match state).
- `OP_RULES_OK` is valid only when matched rules include execution evidence (`command`, `exit_code`, `output_summary`) and no blocking-rule failures.
- Keep a per-run checklist snapshot: `memory/logs/orchestrator_memory_checklist_<run_id>.md`.
- Maintain a run-level **rules audit registry** that accumulates `TASK_RULES_AUDIT` from each synthesizer invocation. This registry is the source for the final Comprehensive Rules Audit Report.

## RLM memory policy

- Disambiguator, Planner and Worker must perform RLM retrieval before their work.
- Reviewer must validate alignment with canonical memory.
- Reflector must use memory to assess if simpler solutions exist in the codebase.
- Refactorer must use memory to find existing utilities before creating new ones.
- For large memory processing, use Sub-LM (`llm_query`/`llm_query_many`) first and pass compact results to cloud reasoning.
- Avoid cloud-side direct summarization of long memory files when Sub-LM extraction is available.
- After each approved task, memory update is mandatory through `synthesizer`.
- At workflow closure, `archivist` must verify memory hygiene and canonical consistency.

## Failure handling

- If required context is missing, issue targeted RLM query and retry once.
- If `test_writer` cannot produce tests, return `TEST_CONTRACT_BLOCKED` for human guidance.
- If Worker fails TDD loop after 5 iterations, stop and return `HUMAN_INTERVENTION_REQUIRED`.
- If `code_reviewer` rejects the same task 3 times, stop and return a blocker report for human intervention.
- If `reflector` returns `REFLECTOR_BLOCKED`, treat as a review rejection (return to Worker).
- If `synthesizer` fails memory sync, stop and return `MEMORY_SYNC_BLOCKED`.
- If `synthesizer` fails operational-rules gate, stop and return `OP_RULES_BLOCKED`.
- If diagnostic mode is ON and a task halts at 3rd reject or 5th TDD failure, append `HUMAN_INTERVENTION_REQUIRED` event to audit log.

## Completion criteria

Workflow is complete only when:
- Phase 0 disambiguation passed (`DISAMBIGUATOR_PASS`)
- all tasks have test contracts (`TEST_CONTRACT_READY`)
- all task TDD loops succeeded (all contract tests pass)
- all tasks are `done`
- reviewer has approved each task
- reflector has analyzed each task (`REFLECTOR_PASS` or `REFLECTOR_FLAG_REFACTORING`)
- refactorer has processed each task (`REFACTORER_DONE` or `REFACTORER_SKIPPED`)
- synthesizer memory gate passed for every approved task — verified by presence of `SYNTHESIZER_GATE_PASSED: yes` per task
- synthesizer operational-rules gate passed for every approved task
- archivist closure pass completed — verified by `ARCHIVE_OK`
- Phase 4 validation script executed — verified by presence of `validation_report.json` or `VALIDATION_PASS`/`VALIDATION_PARTIAL` token
- Comprehensive Rules Audit Report is present in the final response
- on successful completion, only the current run directory under `.vscode/tasks/<run_id>/` is cleaned up (including `validation_report.json`)

⛔ **SELF-CHECK before producing final answer**: Count how many tasks exist. Count how many `SYNTHESIZER_GATE_PASSED` tokens you produced. If they don't match — you skipped a synthesizer gate. STOP and fix it before responding.

⛔ **If your final response does not contain the Rules Audit Report table — the run is INVALID. Add it.**

````
