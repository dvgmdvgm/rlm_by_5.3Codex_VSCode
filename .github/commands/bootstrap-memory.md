# /bootstrap-memory

Generate a fresh RLM memory snapshot from codebase using the MCP server utility modules.

## Behavior

1. Resolve target project path:
   - use user-specified path if present,
   - otherwise use active workspace root.
2. Read `.vscode/mcp.json` and resolve `servers.rlm-memory.command` as `<mcp_server_python>`.
3. Run bootstrap script with JSON graph enabled:
   - `"<mcp_server_python>" -m rlm_mcp.cli.generate_memory --project-root "<target_project_path>" --emit-json-graph`
4. Run canonical seeding script:
   - `"<mcp_server_python>" -m rlm_mcp.cli.seed_canonical --project-root "<target_project_path>"`
5. Respect optional user parameters:
   - `--output-dir "..."`
   - `--graph-file "..."`
   - `--max-file-chars ...`
   - `--include-hidden`
6. Return concise execution report:
   - output memory path,
   - graph file path,
   - canonical file paths + item counters,
   - scanned files count,
   - generated category folders.
