# /save-memory-rule

Expand a short user request into a strict, operational memory rule and persist it into project memory.

## Behavior

1. Parse short user intent (example: "for mobile tasks run BAT build+install after success").
2. Load memory first:
   - `local_memory_bootstrap(question="...", project_path="<active_workspace_root>")`
   - `get_memory_metadata(project_path="<active_workspace_root>", max_files=20, include_headers=false, include_files=false)`
3. Normalize into a strict rule with fields:
   - `scope`, `trigger`, `action`, `preconditions`, `failure_policy`, `evidence`
4. Persist rule in `memory/logs/extracted_facts.jsonl` as active/high-priority extracted_fact.
5. Run `consolidate_memory(project_path="<active_workspace_root>")` immediately.
6. Verify canonical promotion by checking `memory/canonical/coding_rules.md` and `memory/canonical/active_tasks.md` for the saved `RULE_ID` (or unique fingerprint).
7. Return compact confirmation:
   - `RULE_SAVED`, `RULE_ID`, normalized rule summary, updated canonical files.
   - Include `CANONICAL_VERIFIED=yes|no`.

If canonical verification fails after consolidation, return `RULE_SAVED=no` and `BLOCKED: CANONICAL_PROMOTION_FAILED`.

## Example short request

- "В проекте есть BAT для compile+install. Запомни: после каждой успешной mobile-задачи запускай его автоматически."
