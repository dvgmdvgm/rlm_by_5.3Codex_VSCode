---
name: Worker
description: Execution skill for one orchestration task at a time in Antigravity format. Use when a planned task file must be implemented with targeted RLM lookup, minimal code changes, and task-scoped validation.
---

# Worker Skill

## Mission

Execute exactly one task file at a time.

## Mandatory behavior

Before writing code:

- retrieve targeted memory context
- check APIs, signatures, architectural patterns, and relevant prior fixes

Then:

1. read the task file
2. implement the task with minimal scoped changes
3. run targeted validation
4. update task status to `review`
5. report changed files and risks
