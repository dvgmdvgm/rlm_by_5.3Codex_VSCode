"""Real-world compression tests — run all command types and show before/after."""
import sys
import subprocess
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rlm_mcp.output_compressor import compress_output, detect_command_type

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
SEP = "=" * 60


def run_cmd(cmd: str, cwd: str | None = None) -> str:
    """Run shell command, return stdout+stderr."""
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, cwd=cwd or PROJECT_DIR,
            encoding="utf-8", errors="replace",
        )
        out = proc.stdout
        if proc.stderr:
            out += "\n" + proc.stderr
        return out.strip()
    except Exception as e:
        return f"ERROR: {e}"


def test_compression(cmd: str, cmd_type: str | None = None, raw_override: str | None = None):
    """Run command, compress output, print comparison."""
    detected = cmd_type or detect_command_type(cmd)
    raw = raw_override if raw_override is not None else run_cmd(cmd)

    if not raw.strip():
        print(f"\n{SEP}")
        print(f"COMMAND: {cmd}")
        print(f"TYPE: {detected}")
        print("(empty output, skipped)")
        return

    result = compress_output(raw, command_type=detected)

    print(f"\n{SEP}")
    print(f"COMMAND: {cmd}")
    print(f"TYPE: {detected}")
    print(f"{SEP}")
    print(f"--- RAW OUTPUT ({result.original_tokens} tokens, {len(raw)} chars) ---")
    # Show first 500 chars of raw
    if len(raw) > 500:
        print(raw[:500])
        print(f"  ... [{len(raw) - 500} more chars]")
    else:
        print(raw)
    print()
    print(f"--- COMPRESSED ({result.compressed_tokens} tokens, {len(result.compressed)} chars) ---")
    print(result.compressed)
    print()
    print(f"SAVINGS: {result.savings_pct:.1f}% ({result.original_tokens} -> {result.compressed_tokens} tokens)")
    print(f"STRATEGIES: {', '.join(result.strategy_applied)}")


def main():
    print("=" * 60)
    print("  RTK-LIKE TOKEN COMPRESSION — REAL TESTS")
    print("=" * 60)

    # --- TEST 1: git status ---
    print("\n\n### TEST 1: git status")
    test_compression("git status")

    # --- TEST 2: git log ---
    print("\n\n### TEST 2: git log (last 10 commits)")
    test_compression("git log -10")

    # --- TEST 3: git diff ---
    print("\n\n### TEST 3: git diff")
    test_compression("git diff --stat")

    # --- TEST 4: Directory listing ---
    print("\n\n### TEST 4: Directory listing (ls/dir)")
    test_compression("dir /s /b src\\rlm_mcp", cmd_type="ls")

    # --- TEST 5: grep/search ---
    print("\n\n### TEST 5: grep (findstr)")
    test_compression('findstr /s /n "def " src\\rlm_mcp\\*.py', cmd_type="grep")

    # --- TEST 6: Simulated test output (pytest-like) ---
    print("\n\n### TEST 6: Simulated pytest output")
    fake_pytest = """============================= test session starts ==============================
platform win32 -- Python 3.11.5, pytest-7.4.0
rootdir: D:\\project
collected 25 items

tests/test_config.py::test_load_defaults PASSED
tests/test_config.py::test_env_override PASSED
tests/test_config.py::test_missing_field PASSED
tests/test_memory.py::test_read_facts PASSED
tests/test_memory.py::test_write_fact PASSED
tests/test_memory.py::test_deduplicate PASSED
tests/test_memory.py::test_consolidate PASSED
tests/test_compressor.py::test_git_status PASSED
tests/test_compressor.py::test_git_log PASSED
tests/test_compressor.py::test_git_diff PASSED
tests/test_compressor.py::test_ls PASSED
tests/test_compressor.py::test_grep PASSED
tests/test_compressor.py::test_dedup PASSED
tests/test_compressor.py::test_truncate PASSED
tests/test_compressor.py::test_edge_case FAILED
tests/test_compressor.py::test_empty_input PASSED
tests/test_server.py::test_bootstrap PASSED
tests/test_server.py::test_brief PASSED
tests/test_server.py::test_mutation PASSED
tests/test_server.py::test_consolidate PASSED
tests/test_server.py::test_code_index PASSED
tests/test_server.py::test_compress_tool PASSED
tests/test_server.py::test_gain PASSED
tests/test_tracker.py::test_record PASSED
tests/test_tracker.py::test_summary PASSED

FAILURES =======================================================================
_______________________________ test_edge_case ________________________________

    def test_edge_case():
        result = compress_output("", "generic")
>       assert result.compressed_tokens == 0
E       AssertionError: assert 1 == 0

tests/test_compressor.py:142: AssertionError
=========================== short test summary info ============================
FAILED tests/test_compressor.py::test_edge_case - AssertionError: assert 1 == 0
========================= 24 passed, 1 failed in 0.45s ========================"""
    test_compression("pytest", cmd_type="pytest", raw_override=fake_pytest)

    # --- TEST 7: git push simulation ---
    print("\n\n### TEST 7: git push (simulated)")
    fake_push = """Enumerating objects: 15, done.
Counting objects: 100% (15/15), done.
Delta compression using up to 24 threads
Compressing objects: 100% (10/10), done.
Writing objects: 100% (10/10), 5.23 KiB | 2.62 MiB/s, done.
Total 10 (delta 7), reused 0 (delta 0), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (7/7), completed with 5 local objects.
To https://github.com/dvgmdvgm/rlm_by_5.3Codex_VSCode.git
   f991373..abc1234  main -> main"""
    test_compression("git push origin main", cmd_type="git_push", raw_override=fake_push)

    # --- TEST 8: Deduplication (log-like output) ---
    print("\n\n### TEST 8: Deduplication (repeated log lines)")
    fake_log = "\n".join([
        "2026-03-15 10:00:01 INFO  Server started on port 8765",
        "2026-03-15 10:00:02 INFO  Waiting for connection...",
        "2026-03-15 10:00:02 INFO  Waiting for connection...",
        "2026-03-15 10:00:02 INFO  Waiting for connection...",
        "2026-03-15 10:00:02 INFO  Waiting for connection...",
        "2026-03-15 10:00:02 INFO  Waiting for connection...",
        "2026-03-15 10:00:02 INFO  Waiting for connection...",
        "2026-03-15 10:00:02 INFO  Waiting for connection...",
        "2026-03-15 10:00:02 INFO  Waiting for connection...",
        "2026-03-15 10:00:02 INFO  Waiting for connection...",
        "2026-03-15 10:00:02 INFO  Waiting for connection...",
        "2026-03-15 10:00:03 INFO  Client connected: vscode-1",
        "2026-03-15 10:00:04 INFO  Processing request...",
        "2026-03-15 10:00:04 INFO  Processing request...",
        "2026-03-15 10:00:04 INFO  Processing request...",
        "2026-03-15 10:00:04 INFO  Processing request...",
        "2026-03-15 10:00:04 INFO  Processing request...",
        "2026-03-15 10:00:05 INFO  Response sent (200 OK)",
    ])
    test_compression("cat server.log", cmd_type="generic", raw_override=fake_log)

    # --- SUMMARY ---
    print(f"\n\n{'=' * 60}")
    print("  ALL TESTS COMPLETE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
