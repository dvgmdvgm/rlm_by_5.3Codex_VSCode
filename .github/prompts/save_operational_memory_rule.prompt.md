---
agent: agent
description: Expand a short user memory intent into a strict operational rule and persist it into project memory
---

Convert the user's short/approximate memory request into a precise operational rule, then save it to project memory so it is reliably applied in future tasks.

## Required behavior

1. Resolve target `project_path`:
   - if user provided explicit path, use it;
   - otherwise use active workspace root.

2. Load memory context first:
   - call `local_memory_bootstrap(question=<user_request_short_form>, project_path=<project_path>)`
   - call `get_memory_metadata(project_path=<project_path>, max_files=20, include_headers=false, include_files=false)`

3. Normalize the user request into a strict operational rule payload with explicit fields:
   - `scope` (e.g., mobile tasks only)
   - `trigger` (e.g., after APPROVE / task status done)
   - `action` (e.g., run BAT build+install command)
   - `preconditions` (device connected, script exists, path is valid)
   - `failure_policy` (attempt + capture output + report non-blocking unless user says blocking)
   - `evidence` (command, exit code, short output summary)

4. Persist the normalized rule into memory log (`memory/logs/extracted_facts.jsonl`) as `type=extracted_fact` using active status and high priority.

5. Run `consolidate_memory(project_path=<project_path>)` immediately so the rule is promoted into canonical memory in the same workflow run.

6. Mandatory post-check (no skip):
   - reload/read canonical outputs (`memory/canonical/coding_rules.md`, `memory/canonical/active_tasks.md`)
   - verify the saved `RULE_ID` (or equivalent unique rule fingerprint) is present in canonical memory
   - if canonical does not contain the rule after consolidation, return `RULE_SAVED: no` and `BLOCKED` with reason `CANONICAL_PROMOTION_FAILED`

7. Return strict confirmation block:
   - `RULE_SAVED: yes|no`
   - `RULE_ID`
   - `SCOPE`
   - `TRIGGER`
   - `ACTION`
   - `PRECONDITIONS`
   - `FAILURE_POLICY`
   - `CANONICAL_PATHS_UPDATED`
   - `CANONICAL_VERIFIED: yes|no`
   - If impossible to complete, return `BLOCKED` with exact missing data.

## BAT-aware normalization rules

- If user mentions `.bat`, capture script path exactly and store as executable action.
- If user did not provide exact script path, ask one focused clarification question.
- Prefer deterministic local execution command in stored rule (not generic phrasing).

## Safety and precision

- Never claim rule saved unless extracted_facts append + consolidation succeeded + canonical verification passed.
- Do not overwrite unrelated memory entries.
- Keep local-memory-first behavior.
