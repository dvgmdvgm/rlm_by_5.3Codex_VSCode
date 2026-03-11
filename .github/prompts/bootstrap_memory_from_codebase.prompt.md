---
agent: agent
description: Generate RLM memory snapshot from raw codebase using the bootstrap script
---

Run the codebase bootstrap generator script from this repository and create a fresh RLM memory structure for the target project.

## Required behavior

1. Determine target project path:
   - If user explicitly provided a path, use it.
   - Otherwise use current workspace root as target.

2. Resolve the MCP server Python executable from `.vscode/mcp.json`:
   - read `servers.rlm-memory.command`
   - use that executable for all RLM utility commands so the tools are loaded from the MCP server directory, not from the active project.

3. Run script:

```powershell
"<mcp_server_python>" -m rlm_mcp.cli.generate_memory --project-root "<target_project_path>" --emit-json-graph
```

4. After memory generation, seed canonical memory and run consolidation:

```powershell
"<mcp_server_python>" -m rlm_mcp.cli.seed_canonical --project-root "<target_project_path>"
```

5. If user requested custom output path, add:

```powershell
--output-dir "<custom_output_dir>"
```

6. If user requested custom graph file, add:

```powershell
--graph-file "<custom_graph_file>"
```

7. After execution, report:
   - generated memory root path,
   - canonical memory files path and item counters,
   - whether `code_graph.json` exists,
   - scan summary (`Scanned files`, framework hints),
   - first-level generated categories.

8. Do not read old memory as source of truth for this operation; this workflow is code-first bootstrap.
