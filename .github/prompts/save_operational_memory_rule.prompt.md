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

5. Run `consolidate_memory(project_path=<project_path>)` so the rule is promoted into canonical memory.

6. Return strict confirmation block:
   - `RULE_SAVED: yes|no`
   - `RULE_ID`
   - `SCOPE`
   - `TRIGGER`
   - `ACTION`
   - `PRECONDITIONS`
   - `FAILURE_POLICY`
   - `CANONICAL_PATHS_UPDATED`
   - If impossible to complete, return `BLOCKED` with exact missing data.

## BAT-aware normalization rules

- If user mentions `.bat`, capture script path exactly and store as executable action.
- If user did not provide exact script path, ask one focused clarification question.
- Prefer deterministic local execution command in stored rule (not generic phrasing).

## Safety and precision

- Never claim rule saved unless extracted_facts append + consolidation both succeeded.
- Do not overwrite unrelated memory entries.
- Keep local-memory-first behavior.
