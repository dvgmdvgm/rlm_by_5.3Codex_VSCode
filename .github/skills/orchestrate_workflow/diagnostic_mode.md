# Orchestration Diagnostic Mode

## Purpose

Provide verifiable evidence that orchestration stages were executed by role invocation steps.

## Audit artifact

- File: `<run_dir>/orchestration_audit.jsonl`
- One JSON object per event.
- On successful workflow cleanup, preserve a copy in `memory/logs/orchestration_audit_<run_id>.jsonl` before deleting the current run directory.

## Required event fields

- `ts`
- `run_id`
- `task_id`
- `agent_role` (`planner|worker|code_reviewer|synthesizer|archivist`)
- `agent_invocation_id`
- `attempt`
- `event`
- `status`
- `notes`

## Validation checklist

- Planner start/finish events exist.
- Worker/Reviewer events are present for each task.
- `synthesizer_memory_gate_ok` exists after every `APPROVE`.
- `HUMAN_INTERVENTION_REQUIRED` appears on 3rd `REJECT` halt.
- Archivist closure event exists at run end.

## Toggle

- Enable: include `diagnostic:on` in orchestration request.
- Disable: include `diagnostic:off`.
