"""Test venv resolver with real-world Python commands."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rlm_mcp.venv_resolver import resolve_python_command, find_venv

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
SEP = "=" * 60

TEST_CASES = [
    # --- Python executable commands ---
    {"input": "python script.py", "expect_fix": True, "desc": "bare python"},
    {"input": "python3 -m pytest", "expect_fix": True, "desc": "python3 -m module"},
    {"input": "python -c \"print('hello')\"", "expect_fix": True, "desc": "python -c inline"},
    {"input": "python.exe manage.py runserver", "expect_fix": True, "desc": "python.exe"},
    {"input": "py -3 setup.py install", "expect_fix": True, "desc": "py launcher"},

    # --- pip commands ---
    {"input": "pip install requests", "expect_fix": True, "desc": "pip install"},
    {"input": "pip3 list", "expect_fix": True, "desc": "pip3 list"},
    {"input": "pip freeze > requirements.txt", "expect_fix": True, "desc": "pip freeze"},

    # --- pytest ---
    {"input": "pytest tests/ -v", "expect_fix": True, "desc": "pytest"},
    {"input": "pytest --tb=short", "expect_fix": True, "desc": "pytest with args"},

    # --- Other venv tools ---
    {"input": "mypy src/", "expect_fix": True, "desc": "mypy"},
    {"input": "ruff check src/", "expect_fix": True, "desc": "ruff check"},
    {"input": "black --check .", "expect_fix": True, "desc": "black"},
    {"input": "isort --check-only src/", "expect_fix": True, "desc": "isort"},
    {"input": "flake8 src/", "expect_fix": True, "desc": "flake8"},
    {"input": "uvicorn app:main --reload", "expect_fix": True, "desc": "uvicorn"},

    # --- Should NOT be modified ---
    {"input": "git status", "expect_fix": False, "desc": "git (not Python)"},
    {"input": "ls -la", "expect_fix": False, "desc": "ls (not Python)"},
    {"input": "npm install", "expect_fix": False, "desc": "npm (not Python)"},
    {"input": "cargo test", "expect_fix": False, "desc": "cargo (not Python)"},
    {"input": "echo hello", "expect_fix": False, "desc": "echo (not Python)"},
]


def main():
    print(SEP)
    print("  VENV RESOLVER — REAL TESTS")
    print(SEP)

    # Show detected venv
    venv = find_venv(PROJECT_DIR)
    if venv:
        print(f"\n  Detected venv: {venv.venv_dir}")
        print(f"  Python exe:    {venv.python_exe}")
        print(f"  Scripts dir:   {venv.scripts_dir}")
    else:
        print("\n  WARNING: No venv detected! Python tests will not resolve.")
        return 1

    passed = 0
    failed = 0

    for tc in TEST_CASES:
        result = resolve_python_command(tc["input"], PROJECT_DIR)

        ok = True
        if tc["expect_fix"]:
            if not result.was_modified:
                ok = False
        else:
            if result.was_modified:
                ok = False

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        print(f"\n{'-' * 50}")
        print(f"[{status}] {tc['desc']}")
        print(f"  INPUT:    {tc['input']}")
        if result.was_modified:
            print(f"  RESOLVED: {result.resolved}")
            print(f"  TYPE:     {result.resolution_type}")
            print(f"  VENV:     {result.venv_used}")
        else:
            print(f"  (no changes)")

    print(f"\n{SEP}")
    print(f"  RESULTS: {passed} passed, {failed} failed, {len(TEST_CASES)} total")
    print(SEP)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
