# Global MCP Server + Per-Project Memory — 2026-03-02

## META
- id: global_server_per_project_memory_20260302
- updated_at: 2026-03-02T04:30:00Z
- source: user request

### Summary
- Updated VS Code MCP config to run server from fixed global location while binding runtime to active `${workspaceFolder}`.
- `cwd` now uses `${workspaceFolder}` and `RLM_MEMORY_DIR` uses `${workspaceFolder}/memory`.
- Added documentation for multi-project usage without memory mixing.
