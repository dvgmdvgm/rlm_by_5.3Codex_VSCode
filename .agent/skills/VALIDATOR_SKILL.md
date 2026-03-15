---
name: Validator
description: Post-orchestration validation skill for Antigravity. Use after archivist when `validation_report.json` shows missed operational rules and only those missed rules must be executed or explicitly skipped.
---

# Validator Skill

## Mission

Execute only the operational rules that the orchestrator missed during the run.

## Mandatory behavior

1. read `<run_dir>/validation_report.json`
2. if status is pass, return `VALIDATION_PASS`
3. if status is fail, execute only missed rules whose trigger really applied
4. return one of:
   - `VALIDATION_PASS`
   - `VALIDATION_PARTIAL`
   - `VALIDATION_FAIL`
