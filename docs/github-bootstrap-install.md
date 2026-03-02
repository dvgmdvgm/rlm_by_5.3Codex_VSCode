# GitHub One-Command Bootstrap Install

## Goal

Install only the reusable RLM integration assets into a target project from GitHub, without copying MCP server implementation files.

Included by installer:
- `.github` (all Copilot workflows and instructions)
- `scripts/rlm/generate_rlm_memory_from_code.py`
- `scripts/rlm/seed_canonical_from_rlm_memory.py`
- `scripts/rlm/write_orchestrator_memory_checklist.py`

Excluded by installer:
- `src/` (MCP server source code)
- `memory/`
- `backups/`
- `examples/`
- `docs/`
- `prompts/`
- other `scripts/` files (except `rlm/generate_rlm_memory_from_code.py`, `rlm/seed_canonical_from_rlm_memory.py`, and `rlm/write_orchestrator_memory_checklist.py`)
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
git checkout rlm-bootstrap/main -- .github scripts/rlm/generate_rlm_memory_from_code.py scripts/rlm/seed_canonical_from_rlm_memory.py scripts/rlm/write_orchestrator_memory_checklist.py
git remote remove rlm-bootstrap
```

This imports only:
- `.github/`
- `scripts/rlm/generate_rlm_memory_from_code.py`
- `scripts/rlm/seed_canonical_from_rlm_memory.py`
- `scripts/rlm/write_orchestrator_memory_checklist.py`

## Notes

- Installer uses `git clone --depth 1` and copies only the required paths into your target project.
- This is the minimal recommended way to reuse the memory workflow while keeping MCP server global.
- If your target project already has files in these paths, they will be overwritten.
- If target project path does not exist, installer creates it automatically.
- If any git step fails, installer now stops immediately with an explicit error.
- Installer validates that `.github` and `scripts/rlm/generate_rlm_memory_from_code.py` exist in target after copy.
