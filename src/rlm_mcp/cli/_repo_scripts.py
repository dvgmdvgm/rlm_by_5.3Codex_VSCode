from __future__ import annotations

from pathlib import Path
import runpy
import sys


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def repo_script_path(script_name: str) -> Path:
    script_path = _repo_root() / "scripts" / "rlm" / script_name
    if not script_path.exists():
        raise SystemExit(f"RLM server script not found: {script_path}")
    return script_path


def run_repo_script(script_name: str) -> int:
    script_path = repo_script_path(script_name)
    old_argv = sys.argv[:]
    sys.argv = [str(script_path), *sys.argv[1:]]
    try:
        runpy.run_path(str(script_path), run_name="__main__")
    finally:
        sys.argv = old_argv
    return 0
