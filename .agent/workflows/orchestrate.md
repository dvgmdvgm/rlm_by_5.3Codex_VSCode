---
description: Run multi-step work through the Antigravity RLM orchestration workflow.
---

# /orchestrate — Antigravity Orchestration

## Usage

```text
/orchestrate [user request]
```

---

## Execution Steps

### 1. Load the main orchestration skill

Read:

- `.agent/skills/ORCHESTRATE_WORKFLOW_SKILL.md`

### 2. Treat the request as a strict staged orchestration run

Mandatory behavior:

- start with planner
- use worker, code reviewer, synthesizer, archivist, and validator stages
- generate a fresh run directory before planning
- do not bypass reviewer retry limits
- do not bypass the synthesizer gate
- do not bypass archivist or validation
- if orchestration activation fails, return `ORCHESTRATOR_NOT_AVAILABLE`

### 3. Required delegated skills

Load these skills as needed during the run:

- `.agent/skills/PLANNER_SKILL.md`
- `.agent/skills/WORKER_SKILL.md`
- `.agent/skills/CODE_REVIEWER_SKILL.md`
- `.agent/skills/SYNTHESIZER_SKILL.md`
- `.agent/skills/ARCHIVIST_SKILL.md`
- `.agent/skills/VALIDATOR_SKILL.md`

### 4. Response behavior

Return concise progress updates after each completed task and a final condensed summary after validation.
