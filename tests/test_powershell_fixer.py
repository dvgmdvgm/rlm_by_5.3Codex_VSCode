"""Test all 17 PowerShell fix patterns with real-world examples."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rlm_mcp.powershell_fixer import fix_powershell_command

SEP = "=" * 60

TEST_CASES = [
    # --- AUTO-FIX (12 patterns) ---
    {
        "id": "PS-01",
        "name": "&& chain operator",
        "input": "cd src && npm install && npm start",
        "expect_fix": True,
    },
    {
        "id": "PS-02",
        "name": "< angle brackets in hints",
        "input": 'echo "use <file> to add"',
        "expect_fix": True,
    },
    {
        "id": "PS-03",
        "name": "Unquoted path with spaces",
        "input": r"cd C:\My Projects\AI App\src",
        "expect_fix": True,
    },
    {
        "id": "PS-05",
        "name": "export VAR=val",
        "input": "export NODE_ENV=production ; npm start",
        "expect_fix": True,
    },
    {
        "id": "PS-07",
        "name": "grep in pipe",
        "input": 'git log --oneline | grep "feat"',
        "expect_fix": True,
    },
    {
        "id": "PS-08a",
        "name": "head -N",
        "input": "cat logfile.txt | head -20",
        "expect_fix": True,
    },
    {
        "id": "PS-08b",
        "name": "tail -N",
        "input": "Get-Content app.log | tail -5",
        "expect_fix": True,
    },
    {
        "id": "PS-08c",
        "name": "wc -l",
        "input": "dir /s | wc -l",
        "expect_fix": True,
    },
    {
        "id": "PS-09a",
        "name": "rm -rf",
        "input": "rm -rf node_modules",
        "expect_fix": True,
    },
    {
        "id": "PS-09b",
        "name": "mkdir -p",
        "input": "mkdir -p dist/assets/css",
        "expect_fix": True,
    },
    {
        "id": "PS-10",
        "name": "ls -la",
        "input": "ls -la /home/user/project",
        "expect_fix": True,
    },
    {
        "id": "PS-11",
        "name": "touch file",
        "input": "touch newfile.txt",
        "expect_fix": True,
    },
    {
        "id": "PS-12",
        "name": "which command",
        "input": "which python",
        "expect_fix": True,
    },
    {
        "id": "PS-14",
        "name": r"\\n in strings",
        "input": r'echo "line1\nline2\nline3"',
        "expect_fix": True,
    },

    # --- DETECT-ONLY (5 patterns) ---
    {
        "id": "PS-04",
        "name": "heredoc <<EOF",
        "input": "cat <<EOF\nhello world\nEOF",
        "expect_fix": False,
        "expect_warning": True,
    },
    {
        "id": "PS-06",
        "name": "$() subexpression",
        "input": 'echo "today is $(Get-Date)"',
        "expect_fix": False,
        "expect_warning": True,
    },
    {
        "id": "PS-13",
        "name": "Variable in single quotes",
        "input": "echo 'Hello $userName, welcome'",
        "expect_fix": False,
        "expect_warning": True,
    },
    {
        "id": "PS-15",
        "name": "2>&1 wrong order",
        "input": "some-cmd | Out-Null 2>&1",
        "expect_fix": False,
        "expect_warning": True,
    },
    {
        "id": "PS-17",
        "name": "powershell -c subshell",
        "input": 'powershell -c "Get-Process | Select -First 5"',
        "expect_fix": False,
        "expect_warning": True,
    },

    # --- COMBINED (multiple errors in one command) ---
    {
        "id": "COMBO-1",
        "name": "Multiple errors combined",
        "input": "export API_KEY=secret && grep error log.txt | head -10",
        "expect_fix": True,
    },
    {
        "id": "COMBO-2",
        "name": "Bash one-liner disaster",
        "input": 'rm -rf dist && mkdir -p dist/css && touch dist/index.html && ls -la dist',
        "expect_fix": True,
    },
]


def main():
    print(SEP)
    print("  POWERSHELL FIXER — ALL 17 PATTERNS TEST")
    print(SEP)

    passed = 0
    failed = 0

    for tc in TEST_CASES:
        result = fix_powershell_command(tc["input"])

        # Determine test status
        ok = True
        if tc.get("expect_fix"):
            if not result.was_modified:
                ok = False
        if tc.get("expect_warning"):
            if not result.warnings:
                ok = False

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        print(f"\n{'-' * 50}")
        print(f"[{status}] {tc['id']}: {tc['name']}")
        print(f"  INPUT:  {tc['input']}")
        if result.was_modified:
            print(f"  FIXED:  {result.fixed}")
        for fix in result.fixes_applied:
            print(f"  FIX:    {fix['description']}")
        for warn in result.warnings:
            print(f"  WARN:   {warn['description']}")
        if not result.fixes_applied and not result.warnings:
            print(f"  (no changes)")

    print(f"\n{SEP}")
    print(f"  RESULTS: {passed} passed, {failed} failed, {len(TEST_CASES)} total")
    print(SEP)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
