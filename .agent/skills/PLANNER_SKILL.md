---
name: Planner
description: Planning skill for Antigravity orchestration. Use when a large request must be broken into task files and a master plan after loading canonical memory and targeted RLM context.
---

# Planner Skill

## Mission

Take a large user request, recover historical project context from RLM memory, and produce an actionable execution plan with task files.

## Mandatory behavior

Before planning:

1. resolve the active workspace root as `project_path`
2. call `reload_memory_context(project_path=<active_workspace_root>)`
3. call `get_memory_metadata(project_path=<active_workspace_root>)`
4. read canonical memory when available
5. do not produce a final plan until memory lookup is complete

## Outputs

Create inside `<run_dir>/`:

- numbered task files
- `master_plan.md`

Each task file must include objective, inputs, files to modify, steps, acceptance criteria, applied rules, and notes from RLM.
