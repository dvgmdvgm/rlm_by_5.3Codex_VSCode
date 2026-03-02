# GitHub One-Command Bootstrap Install

## Goal

Install only the reusable RLM integration assets into a target project from GitHub, without copying MCP server implementation files.

Included by installer:
- `.github` (all Copilot workflows and instructions)
- `.vscode/mcp.json`
- `scripts/generate_rlm_memory_from_code.py`

Excluded by installer:
- `src/` (MCP server source code)
- `memory/`
- `backups/`
- `examples/`
- `docs/`
- `prompts/`
- other `scripts/` files (except `generate_rlm_memory_from_code.py`)
- `README.md`
- `.venv/`

## One-command run (PowerShell)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([ScriptBlock]::Create((Invoke-WebRequest 'https://raw.githubusercontent.com/dvgmdvgm/rlm_by_5.3Codex_VSCode/main/scripts/install_rlm_bootstrap.ps1' -UseBasicParsing).Content)) -TargetProjectPath 'D:/path/to/your/project'"
```

Example with a real path:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([ScriptBlock]::Create((Invoke-WebRequest 'https://raw.githubusercontent.com/dvgmdvgm/rlm_by_5.3Codex_VSCode/main/scripts/install_rlm_bootstrap.ps1' -UseBasicParsing).Content)) -TargetProjectPath 'D:/AI Projects/MyApp'"
```

## Local run (if repo already cloned)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_rlm_bootstrap.ps1 -TargetProjectPath "D:/path/to/your/project"
```

## Notes

- Installer uses `git sparse-checkout` to fetch only selected paths.
- This is the minimal recommended way to reuse the memory workflow while keeping MCP server global.
- If your target project already has files in these paths, they will be overwritten.
- If target project path does not exist, installer creates it automatically.
