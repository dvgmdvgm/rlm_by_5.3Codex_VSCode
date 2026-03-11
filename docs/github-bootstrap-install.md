# GitHub One-Command Bootstrap Install

## Goal

Install only the reusable RLM integration assets into a target project from GitHub, without copying MCP server implementation files.

Included by installer:
- `.github` (all Copilot workflows and instructions)
- `.vscode/mcp.json`

Excluded by installer:
- `src/` (MCP server source code)
- `scripts/` (RLM utility scripts stay in the MCP server directory and are executed through the server Python interpreter)
- `memory/`
- `backups/`
- `examples/`
- `docs/`
- `prompts/`
- `README.md`
- `.venv/`

## One-command run (PowerShell)

Run directly inside your target project folder (imports into current directory):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([ScriptBlock]::Create((Invoke-WebRequest 'https://raw.githubusercontent.com/dvgmdvgm/rlm_by_5.3Codex_VSCode/main/scripts/rlm/install_rlm_bootstrap.ps1' -UseBasicParsing).Content))"
```

Optional explicit target path:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([ScriptBlock]::Create((Invoke-WebRequest 'https://raw.githubusercontent.com/dvgmdvgm/rlm_by_5.3Codex_VSCode/main/scripts/rlm/install_rlm_bootstrap.ps1' -UseBasicParsing).Content)) -TargetProjectPath 'D:/AI Projects/MyApp'"
```

## Local run (if repo already cloned)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/rlm/install_rlm_bootstrap.ps1
```

## Native git mode (without ps1)

If your target project is already a git repository, run these commands inside that project folder:

```bash
git remote add rlm-bootstrap https://github.com/dvgmdvgm/rlm_by_5.3Codex_VSCode.git
git fetch rlm-bootstrap main --depth=1
git checkout rlm-bootstrap/main -- .github .vscode/mcp.json
git remote remove rlm-bootstrap
```

This imports only:
- `.github/`
- `.vscode/mcp.json`

## Notes

- Installer uses `git clone --depth 1` and copies only the required paths into your target project.
- This is the minimal recommended way to reuse the memory workflow while keeping MCP server global.
- All bootstrap/validator/checklist utilities are run from the MCP server directory by using the Python executable configured in `.vscode/mcp.json`.
- Recommended command pattern: `"<mcp_server_python>" -m rlm_mcp.cli.<tool> ...`
- If your target project already has files in these paths, they will be overwritten.
- If target project path does not exist, installer creates it automatically.
- If any git step fails, installer now stops immediately with an explicit error.
- Installer validates that `.github` and `.vscode/mcp.json` exist in target after copy.
