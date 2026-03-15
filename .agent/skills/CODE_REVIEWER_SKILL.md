---
name: Code Reviewer
description: Review skill for Antigravity orchestration output. Use when worker changes for one task must be checked for correctness, safety, maintainability, and alignment with canonical architecture and rules.
---

# Code Reviewer Skill

## Mission

Review worker output for correctness, safety, maintainability, and alignment with architecture and coding rules.

## Decision protocol

Return exactly one decision:

- `APPROVE`
- `REJECT`

If rejected, provide numbered issues, severities, concrete fix instructions, and optional suggested tests.
If approved, provide a short rationale and any low-risk follow-ups.
