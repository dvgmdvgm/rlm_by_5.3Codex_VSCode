---
name: Save Memory Rule
description: Normalize and persist an operational memory rule in Antigravity format. Use when the user gives a short instruction that should become a strict reusable rule in project memory.
---

# Save Memory Rule Skill

## Mandatory behavior

1. resolve the target project path
2. load memory first with bootstrap and metadata
3. normalize the request into a strict operational rule payload
4. persist it as a strict `extracted_fact`
5. run `consolidate_memory(project_path=<project_path>)`
6. verify canonical promotion before claiming success

## Return format

- `RULE_SAVED: yes|no`
- `RULE_ID`
- normalized summary fields
- `CANONICAL_VERIFIED: yes|no`
- exact blocking reason when save fails
