# Antigravity Gemini workflow layer

This `.agent` folder is the Antigravity-oriented workflow layout.
It follows the structure used by Antigravity Gemini projects: root metadata, direct Markdown skill files in `.agent/skills/`, and workflow entry files in `.agent/workflows/`.

## Structure

- `.agent/skills/*.md` — direct skill definitions for Antigravity
- `.agent/workflows/*.md` — workflow entry files invoked by Antigravity
- `.agent/VERSION` — local format/version marker

## Workflow set

- `orchestrate`
- `bootstrap-memory`
- `save-memory-rule`

## Role skills

- `ORCHESTRATE_WORKFLOW_SKILL.md`
- `PLANNER_SKILL.md`
- `WORKER_SKILL.md`
- `CODE_REVIEWER_SKILL.md`
- `SYNTHESIZER_SKILL.md`
- `ARCHIVIST_SKILL.md`
- `VALIDATOR_SKILL.md`
- `BOOTSTRAP_MEMORY_SKILL.md`
- `SAVE_MEMORY_RULE_SKILL.md`

## Note

This repository is already in Antigravity-first mode.
Keep `.agent/` as the workflow source of truth and use the root `GEMINI.md` file only as a lightweight bridge that points loaders back into `.agent/`.
