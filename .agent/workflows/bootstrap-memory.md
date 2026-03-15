---
description: Generate a fresh RLM memory snapshot from the current codebase in Antigravity workflow format.
---

# /bootstrap-memory — Codebase to Memory

## Usage

```text
/bootstrap-memory [optional path or arguments]
```

---

## Execution Steps

### 1. Load the bootstrap skill

Read:

- `.agent/skills/BOOTSTRAP_MEMORY_SKILL.md`

### 2. Resolve target path

- use the user-specified path if present
- otherwise use the active workspace root

### 3. Execute the code-first memory bootstrap flow

Mandatory behavior:

- resolve the MCP server Python from `.vscode/mcp.json`
- run the memory generator
- run canonical seeding immediately after generation
- include optional output flags when the user provided them

### 4. Return result

Return a concise report with:

- memory root path
- canonical output paths
- item counters
- graph file status
- scan summary
