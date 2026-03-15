"""Real tests for incremental command runner timeout behavior."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rlm_mcp.command_runner import run_command_incremental

PROJECT_DIR = Path(__file__).resolve().parents[1]
PYTHON_EXE = sys.executable
SEP = "=" * 60


def main() -> int:
    print(SEP)
    print("  COMMAND RUNNER — REAL TESTS")
    print(SEP)

    tests = [
        {
            "name": "quick silent exit",
            "command": f'"{PYTHON_EXE}" -c "pass"',
            "kwargs": {"timeout_seconds": 10, "startup_timeout_seconds": 3, "idle_timeout_seconds": 3},
            "expect_timeout": False,
        },
        {
            "name": "quick output",
            "command": f'"{PYTHON_EXE}" -c "print(123)"',
            "kwargs": {"timeout_seconds": 10, "startup_timeout_seconds": 3, "idle_timeout_seconds": 3},
            "expect_timeout": False,
        },
        {
            "name": "startup timeout on silent command",
            "command": f'"{PYTHON_EXE}" -c "import time; time.sleep(2); print(999)"',
            "kwargs": {"timeout_seconds": 10, "startup_timeout_seconds": 1, "idle_timeout_seconds": 3},
            "expect_timeout": True,
            "expect_type": "startup",
        },
        {
            "name": "idle timeout after first output",
            "command": f'"{PYTHON_EXE}" -c "import time; print(111, flush=True); time.sleep(2); print(222, flush=True)"',
            "kwargs": {"timeout_seconds": 10, "startup_timeout_seconds": 3, "idle_timeout_seconds": 1},
            "expect_timeout": True,
            "expect_type": "idle",
        },
        {
            "name": "overall timeout",
            "command": f'"{PYTHON_EXE}" -c "import time; print(1, flush=True); time.sleep(5); print(2, flush=True)"',
            "kwargs": {"timeout_seconds": 2, "startup_timeout_seconds": 3, "idle_timeout_seconds": 10},
            "expect_timeout": True,
            "expect_type": "overall",
        },
    ]

    passed = 0
    failed = 0

    for test in tests:
        result = run_command_incremental(test["command"], cwd=PROJECT_DIR, **test["kwargs"])
        ok = result.timed_out == test["expect_timeout"]
        if test.get("expect_type"):
            ok = ok and result.timeout_type == test["expect_type"]
        if test["name"] == "quick silent exit":
            ok = ok and result.stdout == "" and result.stderr == "" and result.exit_code == 0
        if test["name"] == "quick output":
            ok = ok and result.stdout.strip() == "123"
        if test["name"] == "idle timeout after first output":
            ok = ok and "111" in result.stdout and "222" not in result.stdout

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        print(f"\n{'-' * 50}")
        print(f"[{status}] {test['name']}")
        print(f"  timed_out:    {result.timed_out}")
        print(f"  timeout_type: {result.timeout_type}")
        print(f"  exit_code:    {result.exit_code}")
        print(f"  duration:     {result.duration_sec}s")
        print(f"  stdout:       {result.stdout!r}")
        print(f"  stderr:       {result.stderr!r}")

    print(f"\n{SEP}")
    print(f"  RESULTS: {passed} passed, {failed} failed, {len(tests)} total")
    print(SEP)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
