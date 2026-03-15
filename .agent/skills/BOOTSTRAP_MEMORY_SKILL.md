---
name: Bootstrap Memory
description: Code-first RLM memory bootstrap workflow in Antigravity format. Use when the user asks to generate or regenerate project memory, seed canonical memory, or bootstrap memory artifacts from the current codebase.
---

# Bootstrap Memory Skill

## Mandatory behavior

1. determine the target project path
2. resolve `servers.rlm-memory.command` from `.vscode/mcp.json`
3. run:

```text
"<mcp_server_python>" -m rlm_mcp.cli.generate_memory --project-root "<target_project_path>" --emit-json-graph
```

4. then run:

```text
"<mcp_server_python>" -m rlm_mcp.cli.seed_canonical --project-root "<target_project_path>"
```

5. return output paths, counters, graph status, and scan summary
