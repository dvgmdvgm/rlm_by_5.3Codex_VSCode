# GEMINI.md - Antigravity bridge

This repository now uses the Antigravity-first workflow layout.

## Primary workflow root

Use `.agent/` as the single source of truth:

- `.agent/README.md`
- `.agent/workflows/orchestrate.md`
- `.agent/workflows/bootstrap-memory.md`
- `.agent/workflows/save-memory-rule.md`
- `.agent/skills/*.md`

## Bootstrap rule

Before any response, call `local_memory_bootstrap(question=<user_task>, project_path=<workspace_root>)` and wait for the result.
No exceptions.

Exception: if the prompt already contains `[ORCHESTRATED_SUBAGENT]`, skip bootstrap because context was prepared by the orchestrator.

## Working rules

- Respect `user_response_language` from bootstrap.
- Prefer `.agent/workflows/` and `.agent/skills/` over any legacy layout.
- If canonical memory is needed, read `memory/canonical/architecture.md`, `memory/canonical/coding_rules.md`, and `memory/canonical/active_tasks.md` only as directed by bootstrap.
- Prefer code index tools for symbol discovery.
- For memory writes, append strict `extracted_fact` records and run `consolidate_memory(project_path=<workspace_root>)`.

## Compatibility note

Legacy `.gemini/` and `.agents/` trees are intentionally removed from this repository.
If a Gemini-aware loader enters through `GEMINI.md`, redirect it to `.agent/README.md` and then resolve workflows from `.agent/workflows/`.
