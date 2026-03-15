---
name: Orchestrate Workflow
description: Strict multi-step orchestration for RLM projects in Antigravity format. Use when the user asks for a large feature, migration, refactor, or any task that must be split into planner, worker, code reviewer, synthesizer, archivist, and validator stages with run-directory state tracking.
---

# Orchestrate Workflow Skill

## Purpose

Run autonomous multi-step delivery using a strict staged workflow.

## Stages

- planner
- worker
- code reviewer
- synthesizer
- archivist
- validator

## Mandatory rules

- no batch execution
- no batch review
- no skipping synthesizer after approve
- no skipping archivist at closure
- validate before cleanup

## Run isolation

At the start of every orchestration run, generate a unique `run_id` and `run_dir`:

```text
"<mcp_server_python>" -m rlm_mcp.cli.generate_run_id --project-root "<active_workspace_root>" --create-dir
```

Use the returned JSON as the source of truth.

## Context resilience

After every state transition, update `<run_dir>/orchestrator_state.json`.
Before every new task and before closure, re-read:

- `<run_dir>/orchestrator_state.json`
- `<run_dir>/master_plan.md`

## Stage order

For each task:

1. planner prepares the task set
2. worker implements one task
3. code reviewer approves or rejects
4. synthesizer performs memory sync and rules gate
5. next task starts only after `SYNTHESIZER_GATE_PASSED: yes`

After all tasks:

6. archivist checks closure readiness
7. validator checks for missed operational rules
8. cleanup runs only if all gates passed
