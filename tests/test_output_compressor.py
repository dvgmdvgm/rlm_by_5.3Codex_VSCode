"""Tests for output_compressor — RTK-equivalent CLI output compression."""

import pytest
from rlm_mcp.output_compressor import (
    compress_output,
    deduplicate_lines,
    strip_ansi,
    strip_blank_lines,
    truncate_lines,
    remove_progress_bars,
    detect_command_type,
)


# ---------------------------------------------------------------------------
# Core utility tests
# ---------------------------------------------------------------------------

class TestStripAnsi:
    def test_removes_color_codes(self):
        assert strip_ansi("\x1b[31mERROR\x1b[0m") == "ERROR"

    def test_removes_bold(self):
        assert strip_ansi("\x1b[1mBold text\x1b[0m") == "Bold text"

    def test_no_ansi_passthrough(self):
        assert strip_ansi("plain text") == "plain text"


class TestDeduplicateLines:
    def test_collapses_repeated(self):
        text = "line A\nline A\nline A\nline B"
        result = deduplicate_lines(text, threshold=2)
        assert "line A  (x3)" in result
        assert "line B" in result

    def test_no_dupes(self):
        text = "a\nb\nc"
        result = deduplicate_lines(text, threshold=2)
        assert result == "a\nb\nc"

    def test_short_text_passthrough(self):
        assert deduplicate_lines("hi") == "hi"


class TestTruncateLines:
    def test_short_text_passthrough(self):
        text = "a\nb\nc"
        assert truncate_lines(text, max_lines=10) == text

    def test_long_text_truncated(self):
        lines = [f"line {i}" for i in range(300)]
        text = "\n".join(lines)
        result = truncate_lines(text, max_lines=50, tail=10)
        assert "omitted" in result
        assert "line 0" in result
        assert "line 299" in result


class TestRemoveProgressBars:
    def test_removes_tqdm(self):
        text = "downloading\n50%|#####     | 50/100\ndone"
        result = remove_progress_bars(text)
        assert "50%" not in result
        assert "done" in result

    def test_removes_git_progress(self):
        text = "Receiving objects: 100% (50/50), done."
        result = remove_progress_bars(text)
        assert result.strip() == ""


class TestStripBlankLines:
    def test_collapses_blanks(self):
        text = "a\n\n\n\n\nb"
        result = strip_blank_lines(text)
        assert result == "a\n\nb"


# ---------------------------------------------------------------------------
# Git command tests
# ---------------------------------------------------------------------------

class TestGitStatus:
    def test_clean_repo(self):
        output = """On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean"""
        result = compress_output("git status", output)
        assert result.compressed_lines < result.original_lines
        assert "main" in result.compressed
        assert "clean" in result.compressed.lower() or "nothing to commit" in result.compressed

    def test_with_changes(self):
        output = """On branch develop
Your branch is ahead of 'origin/develop' by 2 commits.
  (use "git push" to publish your local commits)

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        modified:   src/main.py
        new file:   src/utils.py

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
        modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        temp.txt
        debug.log"""
        result = compress_output("git status", output)
        assert "staged (2)" in result.compressed
        assert "unstaged (1)" in result.compressed
        assert "untracked (2)" in result.compressed
        assert "(use " not in result.compressed
        assert result.savings_pct > 30


class TestGitLog:
    def test_standard_log(self):
        output = """commit abc1234567890
Author: Test User <test@example.com>
Date:   Mon Mar 15 10:30:00 2026 +0100

    Fix bug in parser

commit def9876543210
Author: Test User <test@example.com>
Date:   Sun Mar 14 09:15:00 2026 +0100

    Add new feature

commit 1111111222222
Author: Other Dev <dev@example.com>
Date:   Sat Mar 13 08:00:00 2026 +0100

    Initial commit"""
        result = compress_output("git log", output)
        assert "abc1234" in result.compressed
        assert "Fix bug" in result.compressed
        assert "Author:" not in result.compressed
        assert result.savings_pct > 20

    def test_oneline_format(self):
        output = """abc1234 Fix bug\ndef5678 Add feature\n1111111 Initial"""
        result = compress_output("git log --oneline -n 5", output)
        assert "abc1234" in result.compressed


class TestGitDiff:
    def test_strips_index_lines(self):
        output = """diff --git a/file.py b/file.py
index abc1234..def5678 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 line1
+new line
 line2
 line3"""
        result = compress_output("git diff", output)
        assert "index " not in result.compressed
        assert "+new line" in result.compressed


class TestGitPush:
    def test_push_success(self):
        output = """Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 8 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 350 bytes | 350.00 KiB/s, done.
Total 3 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
To github.com:user/repo.git
   abc1234..def5678  main -> main"""
        result = compress_output("git push", output)
        assert "ok" in result.compressed.lower()
        assert "main" in result.compressed
        assert "Enumerating" not in result.compressed
        assert result.savings_pct > 70

    def test_push_up_to_date(self):
        result = compress_output("git push", "Everything up-to-date")
        assert "up-to-date" in result.compressed

    def test_pull_with_changes(self):
        output = """remote: Enumerating objects: 10, done.
remote: Counting objects: 100% (10/10), done.
remote: Compressing objects: 100% (6/6), done.
Updating abc1234..def5678
 3 files changed, 10 insertions(+), 2 deletions(-)"""
        result = compress_output("git pull", output)
        assert "3" in result.compressed
        assert "+10" in result.compressed


class TestGitAdd:
    def test_silent(self):
        result = compress_output("git add .", "")
        assert result.compressed == ""

    def test_add_ok(self):
        result = compress_output("git add file.py", "")
        assert result.compressed_chars == 0


class TestGitCommit:
    def test_success(self):
        output = "[main abc1234] Fix bug\n 1 file changed, 2 insertions(+), 1 deletion(-)"
        result = compress_output("git commit -m 'Fix bug'", output)
        assert "abc1234" in result.compressed


# ---------------------------------------------------------------------------
# Test runner tests
# ---------------------------------------------------------------------------

class TestTestOutputCompression:
    def test_all_pass_cargo(self):
        output = """running 15 tests
test utils::test_parse ... ok
test utils::test_format ... ok
test utils::test_validate ... ok
test main::test_run ... ok
test main::test_init ... ok
test main::test_config ... ok
test main::test_build ... ok
test main::test_clean ... ok
test main::test_install ... ok
test main::test_uninstall ... ok
test core::test_a ... ok
test core::test_b ... ok
test core::test_c ... ok
test core::test_d ... ok
test core::test_e ... ok

test result: ok. 15 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out

   Doc-tests my_crate

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out"""
        result = compress_output("cargo test", output)
        assert "PASSED" in result.compressed or "ok" in result.compressed.lower()
        assert result.savings_pct > 50

    def test_with_failures(self):
        output = """running 5 tests
test test_a ... ok
test test_b ... ok
test test_c ... FAILED
test test_d ... ok
test test_e ... FAILED

failures:

---- test_c stdout ----
thread 'test_c' panicked at 'assertion failed: x == y'

---- test_e stdout ----
thread 'test_e' panicked at 'overflow error'

test result: FAILED. 3 passed; 2 failed; 0 ignored"""
        result = compress_output("cargo test", output)
        assert "FAIL" in result.compressed
        assert "panic" in result.compressed or "assertion" in result.compressed

    def test_pytest_pass(self):
        output = """============================= test session starts =============================
collected 20 items

tests/test_a.py::test_1 PASSED
tests/test_a.py::test_2 PASSED
tests/test_b.py::test_3 PASSED

============================= 20 passed in 1.23s =============================="""
        result = compress_output("pytest", output)
        assert "PASSED" in result.compressed or "passed" in result.compressed
        assert result.savings_pct > 30


# ---------------------------------------------------------------------------
# Build & Lint tests
# ---------------------------------------------------------------------------

class TestBuildLint:
    def test_eslint_errors(self):
        output = """
/src/App.tsx:5:10: error: 'useState' is defined but never used
/src/App.tsx:12:5: warning: Unexpected console statement
/src/utils.ts:3:1: error: Missing semicolon
/src/utils.ts:8:3: error: Unexpected token
"""
        result = compress_output("eslint src/", output)
        assert "ERRORS" in result.compressed
        assert "App.tsx" in result.compressed
        assert "utils.ts" in result.compressed

    def test_tsc_errors(self):
        output = """src/index.ts:10:5: error TS2322: Type 'string' is not assignable
src/index.ts:15:3: error TS2345: Argument of type 'number'"""
        result = compress_output("tsc --noEmit", output)
        assert "ERRORS" in result.compressed

    def test_prettier_all_good(self):
        result = compress_output("prettier --check .", "All matched files use Prettier code style!")
        assert "ok" in result.compressed.lower()

    def test_cargo_build_clean(self):
        output = """   Compiling serde v1.0.196
   Compiling tokio v1.36.0
   Compiling my-app v0.1.0
    Finished dev [unoptimized + debuginfo] target(s) in 45.32s"""
        result = compress_output("cargo build", output)
        assert "Compiling serde" not in result.compressed


# ---------------------------------------------------------------------------
# File command tests
# ---------------------------------------------------------------------------

class TestFileCommands:
    def test_ls_compact(self):
        lines = [f"drwxr-xr-x  2 user staff 64 Jan  1 12:00 dir{i}" for i in range(20)]
        lines += [f"-rw-r--r--  1 user staff 1234 Jan  1 12:00 file{i}.txt" for i in range(20)]
        output = "\n".join(lines)
        result = compress_output("ls -la", output)
        assert result.compressed_lines <= result.original_lines
        assert "dir0/" in result.compressed

    def test_grep_grouped(self):
        output = "\n".join([
            f"src/main.py:{i}:match {i}" for i in range(1, 25)
        ] + [
            f"src/utils.py:{i}:match {i}" for i in range(1, 15)
        ])
        result = compress_output("grep -rn pattern .", output)
        assert "main.py" in result.compressed
        assert "matches" in result.compressed.lower()

    def test_cat_truncated(self):
        lines = [f"# Comment line {i}" for i in range(50)]
        lines += [f"code_line_{i} = {i}" for i in range(200)]
        output = "\n".join(lines)
        result = compress_output("cat largefile.py", output)
        assert result.compressed_lines <= result.original_lines


# ---------------------------------------------------------------------------
# Container tests
# ---------------------------------------------------------------------------

class TestContainers:
    def test_docker_ps(self):
        output = """CONTAINER ID   IMAGE          COMMAND   CREATED   STATUS    PORTS   NAMES
abc123   nginx:latest   "nginx"   2h ago    Up 2h     80/tcp  web
def456   redis:7        "redis"   3h ago    Up 3h     6379    cache"""
        result = compress_output("docker ps", output)
        assert "2 containers" in result.compressed
        assert "CONTAINER ID" not in result.compressed

    def test_docker_logs_dedup(self):
        lines = ["[INFO] Server started"] * 50 + ["[ERROR] Connection timeout"] * 3
        output = "\n".join(lines)
        result = compress_output("docker logs web", output)
        assert "x50" in result.compressed or "(x50)" in result.compressed
        assert result.savings_pct > 70


# ---------------------------------------------------------------------------
# Package manager tests
# ---------------------------------------------------------------------------

class TestPackageManagers:
    def test_pip_list(self):
        output = """Package         Version
--------------- -------
pip             24.0
setuptools      69.0.3
requests        2.31.0
numpy           1.26.0"""
        result = compress_output("pip list", output)
        assert "pip==24.0" in result.compressed
        assert "4 packages" in result.compressed
        assert "-------" not in result.compressed

    def test_pip_outdated(self):
        output = """Package    Version Latest Type
---------- ------- ------ -----
pip        24.0    24.1   wheel
setuptools 69.0    70.0   wheel"""
        result = compress_output("pip list --outdated", output)
        assert "pip:" in result.compressed
        assert "->" in result.compressed


# ---------------------------------------------------------------------------
# Data & Analytics tests
# ---------------------------------------------------------------------------

class TestDataAnalytics:
    def test_curl_json_auto_detect(self):
        output = '{"name": "test", "items": [1, 2, 3], "nested": {"key": "value"}}'
        result = compress_output("curl https://api.example.com", output)
        assert "JSON" in result.compressed or "<str>" in result.compressed

    def test_curl_with_progress_stripped(self):
        output = """  % Total    % Received % Xferd
 100  1234  100  1234    0     0  12340      0
{"result": "ok"}"""
        result = compress_output("curl -o - https://example.com", output)
        # Should not contain progress percentage
        assert "Xferd" not in result.compressed


# ---------------------------------------------------------------------------
# GitHub CLI tests
# ---------------------------------------------------------------------------

class TestGitHubCLI:
    def test_gh_pr_list(self):
        output = """#123  Fix login bug    main  OPEN
#124  Add dark mode    dev   MERGED
#125  Update deps      main  CLOSED"""
        result = compress_output("gh pr list", output)
        assert "#123" in result.compressed

    def test_gh_issue_list(self):
        output = """#10  Bug in parser    open   2026-03-15
#11  Feature request  open   2026-03-14"""
        result = compress_output("gh issue list", output)
        assert "#10" in result.compressed


# ---------------------------------------------------------------------------
# Detection & edge case tests
# ---------------------------------------------------------------------------

class TestDetection:
    def test_detects_git_status(self):
        assert "git" in detect_command_type("git status")

    def test_detects_cargo_test(self):
        assert "cargo" in detect_command_type("cargo test --release")

    def test_detects_docker_ps(self):
        assert "docker" in detect_command_type("docker ps -a")

    def test_unknown_command(self):
        assert detect_command_type("some_random_command") == "unknown"


class TestEdgeCases:
    def test_empty_output(self):
        result = compress_output("any command", "")
        assert result.command_type == "empty"
        assert result.savings_pct == 0.0

    def test_none_output(self):
        result = compress_output("cmd", None)  # type: ignore
        assert result.compressed_chars == 0

    def test_unknown_command_passthrough(self):
        output = "some output here"
        result = compress_output("unknown_tool --flag", output)
        assert result.command_type == "unknown"
        assert result.compressed == output

    def test_very_large_output(self):
        """Ensure large outputs don't crash."""
        lines = [f"line {i}: " + "x" * 100 for i in range(5000)]
        output = "\n".join(lines)
        result = compress_output("cargo test", output)
        assert result.compressed_lines < result.original_lines
        assert result.savings_pct > 0


# ---------------------------------------------------------------------------
# Integration: savings percentages
# ---------------------------------------------------------------------------

class TestSavingsPercentages:
    def test_git_push_savings(self):
        output = """Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 8 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 350 bytes | 350.00 KiB/s, done.
Total 3 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
To github.com:user/repo.git
   abc1234..def5678  main -> main"""
        result = compress_output("git push", output)
        assert result.savings_pct >= 60, f"Expected >=60% savings, got {result.savings_pct}%"

    def test_test_pass_savings(self):
        lines = [f"test test_{i} ... ok" for i in range(50)]
        lines.append("test result: ok. 50 passed; 0 failed; 0 ignored")
        output = "\n".join(lines)
        result = compress_output("cargo test", output)
        assert result.savings_pct >= 50, f"Expected >=50% savings, got {result.savings_pct}%"

    def test_docker_logs_dedup_savings(self):
        lines = ["[INFO] Processing request"] * 200
        output = "\n".join(lines)
        result = compress_output("docker logs app", output)
        assert result.savings_pct >= 80, f"Expected >=80% savings, got {result.savings_pct}%"
