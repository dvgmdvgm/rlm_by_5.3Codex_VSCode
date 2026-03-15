---
description: Normalize a short operational-memory request into a strict saved rule in Antigravity workflow format.
---

# /save-memory-rule — Persist Operational Rule

## Usage

```text
/save-memory-rule [rule request]
```

---

## Execution Steps

### 1. Load the save-memory-rule skill

Read:

- `.agent/skills/SAVE_MEMORY_RULE_SKILL.md`

### 2. Normalize the request

Mandatory behavior:

- resolve the target project path
- load memory first
- normalize the request into a strict operational rule payload
- persist it as a strict `extracted_fact`
- run `consolidate_memory` immediately
- verify canonical promotion before claiming success

### 3. Return result

Return:

- `RULE_SAVED: yes|no`
- `RULE_ID`
- normalized rule summary
- canonical verification result
- exact blocking reason when save fails
