"""Virtual environment resolver — auto-detect and route Python commands through venv.

Solves the retry problem:
  LLM: `python script.py`     → fails (no system Python)
  LLM: finds .venv             → extra call
  LLM: activates .venv         → extra call
  LLM: re-runs command         → finally works (3 wasted calls)

With this module:
  LLM: `python script.py`     → auto-resolved to `.venv/Scripts/python.exe script.py` → works first time
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Standard venv directory names to probe (in priority order)
_VENV_CANDIDATES = [".venv", "venv", "env", ".env", ".virtualenv"]

# Python commands that should be routed through venv
_PYTHON_CMD_RE = re.compile(
    r"^(?:&\s+)?"                     # optional PS call operator
    r"(?:\"[^\"]*?python[^\"]*\"\s+|"  # quoted python path
    r"python[23]?(?:\.exe)?\s+|"       # python / python3 / python.exe
    r"py\s+(?:-\d\s+)?)"              # py -3
)

# pip/pytest/etc that are venv scripts
_VENV_SCRIPT_RE = re.compile(
    r"^(?:&\s+)?"
    r"(?:pip[3]?|pytest|mypy|ruff|black|isort|flake8|pylint|"
    r"uvicorn|gunicorn|flask|django-admin|celery|"
    r"pre-commit|tox|nox|poetry|pdm|hatch)"
    r"(?:\.exe)?\s"
)

# python -m module pattern
_PYTHON_M_RE = re.compile(
    r"^(?:&\s+)?(?:python[23]?(?:\.exe)?)\s+-m\s+"
)


@dataclass
class VenvInfo:
    """Resolved virtual environment information."""
    venv_dir: Path
    python_exe: Path
    scripts_dir: Path
    is_windows: bool

    def to_dict(self) -> dict[str, str]:
        return {
            "venv_dir": str(self.venv_dir),
            "python_exe": str(self.python_exe),
            "scripts_dir": str(self.scripts_dir),
        }


@dataclass
class VenvResolveResult:
    """Result of resolving a command through venv."""
    original: str
    resolved: str
    was_modified: bool
    venv_used: str | None = None
    resolution_type: str | None = None  # "python_exe", "venv_script", "activate"

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"command": self.resolved, "was_modified": self.was_modified}
        if self.venv_used:
            result["venv_used"] = self.venv_used
        if self.resolution_type:
            result["resolution_type"] = self.resolution_type
        return result


def find_venv(project_path: str | Path) -> VenvInfo | None:
    """Find virtual environment in project directory.

    Searches for standard venv directory names (.venv, venv, env, etc.)
    and validates that the Python executable exists.
    """
    project = Path(project_path)
    is_windows = os.name == "nt"

    for candidate in _VENV_CANDIDATES:
        venv_dir = project / candidate
        if not venv_dir.is_dir():
            continue

        # Check for Python executable
        if is_windows:
            scripts_dir = venv_dir / "Scripts"
            python_exe = scripts_dir / "python.exe"
        else:
            scripts_dir = venv_dir / "bin"
            python_exe = scripts_dir / "python"

        if python_exe.exists():
            return VenvInfo(
                venv_dir=venv_dir,
                python_exe=python_exe,
                scripts_dir=scripts_dir,
                is_windows=is_windows,
            )

    return None


def _quote_path(path: Path) -> str:
    """Quote path if it contains spaces."""
    s = str(path)
    if " " in s and not s.startswith('"'):
        return f'"{s}"'
    return s


def _resolve_python_command(cmd: str, venv: VenvInfo) -> tuple[str, str]:
    """Replace `python ...` with venv python executable path."""
    python_quoted = _quote_path(venv.python_exe)

    # Match and replace by finding the prefix end position, then concatenating
    patterns = [
        # & "python" args  or  & python args
        re.compile(r'^&\s+"?python[23]?(?:\.exe)?"?\s+'),
        # python3.exe args
        re.compile(r'^python[23]?(?:\.exe)?\s+'),
        # py -3 args
        re.compile(r'^py\s+(?:-\d\s+)?'),
    ]

    for pattern in patterns:
        m = pattern.match(cmd)
        if m:
            rest = cmd[m.end():]
            if cmd.startswith("&"):
                resolved = f"& {python_quoted} {rest}"
            else:
                resolved = f"{python_quoted} {rest}"
            return resolved, "python_exe"

    return cmd, ""


def _resolve_venv_script(cmd: str, venv: VenvInfo) -> tuple[str, str]:
    """Replace `pip ...` / `pytest ...` etc with venv script path."""
    match = _VENV_SCRIPT_RE.match(cmd)
    if not match:
        return cmd, ""

    # Extract the script name
    prefix = match.group(0).strip()
    # Remove optional & call operator
    script_name = re.sub(r'^&\s+', '', prefix).strip()

    # Find the script in venv Scripts/bin directory
    if venv.is_windows:
        script_path = venv.scripts_dir / f"{script_name}.exe"
        if not script_path.exists():
            script_path = venv.scripts_dir / script_name
    else:
        script_path = venv.scripts_dir / script_name

    if script_path.exists():
        script_quoted = _quote_path(script_path)
        rest = cmd[match.end():]
        resolved = f"& {script_quoted} {rest}" if venv.is_windows else f"{script_quoted} {rest}"
        return resolved, "venv_script"

    # Fallback: use python -m <module>
    python_quoted = _quote_path(venv.python_exe)
    rest = cmd[match.end():]
    resolved = f"{python_quoted} -m {script_name} {rest}"
    return resolved, "python_m_fallback"


def resolve_python_command(
    command: str,
    project_path: str | Path,
) -> VenvResolveResult:
    """Resolve a command through the project's virtual environment.

    If the command uses python/pip/pytest/etc. and a .venv exists,
    the command is rewritten to use the venv's executables directly.

    This eliminates the LLM retry cycle of:
    1. Try `python` → fails (not in PATH)
    2. Find .venv → extra call
    3. Activate → extra call
    4. Re-run → finally works
    """
    # Find venv
    venv = find_venv(project_path)
    if not venv:
        return VenvResolveResult(
            original=command,
            resolved=command,
            was_modified=False,
        )

    # Try python command resolution
    if _PYTHON_CMD_RE.match(command) or _PYTHON_M_RE.match(command):
        resolved, rtype = _resolve_python_command(command, venv)
        if rtype:
            return VenvResolveResult(
                original=command,
                resolved=resolved,
                was_modified=True,
                venv_used=str(venv.venv_dir),
                resolution_type=rtype,
            )

    # Try venv script resolution (pip, pytest, etc.)
    if _VENV_SCRIPT_RE.match(command):
        resolved, rtype = _resolve_venv_script(command, venv)
        if rtype:
            return VenvResolveResult(
                original=command,
                resolved=resolved,
                was_modified=True,
                venv_used=str(venv.venv_dir),
                resolution_type=rtype,
            )

    return VenvResolveResult(
        original=command,
        resolved=command,
        was_modified=False,
    )
