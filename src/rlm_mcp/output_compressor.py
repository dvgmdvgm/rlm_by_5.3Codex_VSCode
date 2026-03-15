"""Output compressor — RTK-like token reduction for shell command output.

Four compression strategies applied per command type:
1. Smart Filtering   — remove noise (ANSI codes, progress bars, blank lines, boilerplate)
2. Grouping          — aggregate similar items (files by dir, errors by type)
3. Truncation        — keep relevant context, cut redundancy
4. Deduplication     — collapse repeated log lines with counts
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Compression result
# ---------------------------------------------------------------------------

@dataclass
class CompressionResult:
    """Result of compressing command output."""
    original: str
    compressed: str
    original_tokens: int
    compressed_tokens: int
    savings_pct: float
    strategy_applied: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "compressed_output": self.compressed,
            "token_stats": {
                "original_tokens": self.original_tokens,
                "compressed_tokens": self.compressed_tokens,
                "savings_pct": round(self.savings_pct, 1),
            },
            "strategies": self.strategy_applied,
        }


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token (same as server.py)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Strategy 1: Smart Filtering
# ---------------------------------------------------------------------------

# ANSI escape codes
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# Carriage-return based progress bars (e.g. pip, cargo)
_PROGRESS_RE = re.compile(r"^.*\r(?!\n).*$", re.MULTILINE)

# Spinner/progress characters
_SPINNER_RE = re.compile(r"^[\s]*[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏|/\-\\]+\s*$", re.MULTILINE)

# npm/pip download progress lines
_DOWNLOAD_PROGRESS_RE = re.compile(
    r"^.*(Downloading|Collecting|Installing|Resolving|Extracting).*\d+%.*$",
    re.MULTILINE | re.IGNORECASE,
)

# Git object counting/compressing lines
_GIT_PROGRESS_RE = re.compile(
    r"^(remote: )?(Enumerating|Counting|Compressing|Receiving|Resolving|Writing|Total|Delta).*$",
    re.MULTILINE,
)

# Blank line runs (more than 2 consecutive)
_BLANK_RUNS_RE = re.compile(r"\n{3,}", re.MULTILINE)

# Common boilerplate lines
_BOILERPLATE_PATTERNS = [
    re.compile(r"^\s*#.*$", re.MULTILINE),                # shell comments
    re.compile(r"^={3,}$", re.MULTILINE),                  # separator lines ===
    re.compile(r"^-{3,}$", re.MULTILINE),                  # separator lines ---
    re.compile(r"^\s*$", re.MULTILINE),                     # empty lines
]


def smart_filter(text: str) -> tuple[str, list[str]]:
    """Remove noise: ANSI codes, progress bars, spinners, excessive blanks."""
    applied: list[str] = []
    result = text

    # Strip ANSI
    if _ANSI_RE.search(result):
        result = _ANSI_RE.sub("", result)
        applied.append("strip_ansi")

    # Remove progress bars/spinners
    for pattern, name in [
        (_PROGRESS_RE, "strip_progress"),
        (_SPINNER_RE, "strip_spinners"),
        (_DOWNLOAD_PROGRESS_RE, "strip_download_progress"),
        (_GIT_PROGRESS_RE, "strip_git_progress"),
    ]:
        if pattern.search(result):
            result = pattern.sub("", result)
            applied.append(name)

    # Collapse blank runs
    prev_len = len(result)
    result = _BLANK_RUNS_RE.sub("\n\n", result)
    if len(result) < prev_len:
        applied.append("collapse_blanks")

    # Strip trailing whitespace per line
    lines = [line.rstrip() for line in result.split("\n")]
    result = "\n".join(lines).strip()

    return result, applied


# ---------------------------------------------------------------------------
# Strategy 2: Grouping
# ---------------------------------------------------------------------------

def group_by_directory(lines: list[str]) -> str:
    """Group file paths by their parent directory."""
    from collections import defaultdict
    dirs: dict[str, list[str]] = defaultdict(list)
    other: list[str] = []

    for line in lines:
        stripped = line.strip()
        if "/" in stripped or "\\" in stripped:
            # Looks like a file path
            parts = stripped.replace("\\", "/").rsplit("/", 1)
            if len(parts) == 2:
                dirs[parts[0]].append(parts[1])
            else:
                other.append(stripped)
        else:
            other.append(stripped)

    result_parts: list[str] = []
    for dir_name, files in sorted(dirs.items()):
        result_parts.append(f"{dir_name}/ ({len(files)} files)")
        for f in sorted(files)[:10]:  # cap at 10 per dir
            result_parts.append(f"  {f}")
        if len(files) > 10:
            result_parts.append(f"  ... +{len(files) - 10} more")

    result_parts.extend(other)
    return "\n".join(result_parts)


def group_errors_by_type(lines: list[str]) -> str:
    """Group error/warning lines by their type prefix."""
    from collections import defaultdict
    groups: dict[str, list[str]] = defaultdict(list)
    other: list[str] = []

    error_pattern = re.compile(r"^(error|warning|info|note|hint)\[?[A-Z0-9]*\]?:?\s*", re.IGNORECASE)

    for line in lines:
        match = error_pattern.match(line.strip())
        if match:
            etype = match.group(1).lower()
            rest = line.strip()[match.end():]
            groups[etype].append(rest)
        else:
            other.append(line)

    result_parts: list[str] = []
    for etype in ["error", "warning", "info", "note", "hint"]:
        if etype in groups:
            items = groups[etype]
            result_parts.append(f"{etype.upper()} ({len(items)}):")
            for item in items[:15]:  # cap
                result_parts.append(f"  {item}")
            if len(items) > 15:
                result_parts.append(f"  ... +{len(items) - 15} more")

    result_parts.extend(other)
    return "\n".join(result_parts)


# ---------------------------------------------------------------------------
# Strategy 3: Truncation
# ---------------------------------------------------------------------------

def truncate_output(text: str, max_lines: int = 80, context_lines: int = 5) -> tuple[str, bool]:
    """Keep first/last context lines, truncate middle if too long."""
    lines = text.split("\n")
    if len(lines) <= max_lines:
        return text, False

    head = lines[:context_lines]
    tail = lines[-context_lines:]
    omitted = len(lines) - 2 * context_lines

    return "\n".join(head + [f"... ({omitted} lines omitted) ..."] + tail), True


# ---------------------------------------------------------------------------
# Strategy 4: Deduplication
# ---------------------------------------------------------------------------

def deduplicate_lines(text: str, min_count: int = 3) -> tuple[str, int]:
    """Collapse consecutive identical/similar lines with count."""
    lines = text.split("\n")
    result: list[str] = []
    prev_line: str | None = None
    count = 1
    total_deduped = 0

    for line in lines:
        normalized = line.strip()
        if normalized == prev_line and normalized:
            count += 1
        else:
            if prev_line is not None:
                if count >= min_count:
                    result.append(f"{prev_line}  (x{count})")
                    total_deduped += count - 1
                else:
                    result.extend([prev_line] * count)
            prev_line = normalized
            count = 1

    # Flush last
    if prev_line is not None:
        if count >= min_count:
            result.append(f"{prev_line}  (x{count})")
            total_deduped += count - 1
        else:
            result.extend([prev_line] * count)

    return "\n".join(result), total_deduped


# ---------------------------------------------------------------------------
# Git-specific compressors
# ---------------------------------------------------------------------------

def compress_git_status(raw: str) -> str:
    """Compact git status output into categories."""
    lines = raw.strip().split("\n")
    staged: list[str] = []
    modified: list[str] = []
    untracked: list[str] = []
    other: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("On branch") or stripped.startswith("Your branch"):
            # Extract branch info
            if stripped.startswith("On branch"):
                other.insert(0, stripped)
            continue
        if stripped.startswith("(use"):
            continue  # skip hint lines

        # Parse git status short codes
        if stripped.startswith("new file:"):
            staged.append(stripped.replace("new file:", "").strip())
        elif stripped.startswith("modified:"):
            modified.append(stripped.replace("modified:", "").strip())
        elif stripped.startswith("deleted:"):
            modified.append(f"(del) {stripped.replace('deleted:', '').strip()}")
        elif stripped.startswith("renamed:"):
            modified.append(f"(ren) {stripped.replace('renamed:', '').strip()}")
        elif "Changes to be committed" in stripped or "Changes not staged" in stripped or "Untracked files" in stripped:
            continue  # skip section headers
        else:
            untracked.append(stripped)

    parts: list[str] = []
    for label_items in other:
        parts.append(label_items)

    if staged:
        parts.append(f"staged ({len(staged)}): {', '.join(staged[:8])}")
        if len(staged) > 8:
            parts.append(f"  +{len(staged) - 8} more")
    if modified:
        parts.append(f"modified ({len(modified)}): {', '.join(modified[:8])}")
        if len(modified) > 8:
            parts.append(f"  +{len(modified) - 8} more")
    if untracked:
        parts.append(f"untracked ({len(untracked)}): {', '.join(untracked[:8])}")
        if len(untracked) > 8:
            parts.append(f"  +{len(untracked) - 8} more")

    if not staged and not modified and not untracked:
        parts.append("clean")

    return "\n".join(parts)


def compress_git_log(raw: str) -> str:
    """One-line-per-commit format."""
    lines = raw.strip().split("\n")
    commits: list[str] = []
    current_hash = ""
    current_msg = ""
    current_date = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("commit "):
            if current_hash:
                commits.append(f"{current_hash[:7]} {current_date} {current_msg}")
            current_hash = stripped.split()[1] if len(stripped.split()) > 1 else ""
            current_msg = ""
            current_date = ""
        elif stripped.startswith("Date:"):
            current_date = stripped[5:].strip()[:16]  # short date
        elif stripped.startswith("Author:"):
            continue
        elif stripped.startswith("Merge:"):
            continue
        elif stripped and not current_msg:
            current_msg = stripped

    if current_hash:
        commits.append(f"{current_hash[:7]} {current_date} {current_msg}")

    return "\n".join(commits)


def compress_git_diff(raw: str) -> str:
    """Condensed diff: file path + changes summary.
    
    Handles both full diff output and --stat output.
    """
    lines = raw.strip().split("\n")

    # Detect --stat format:  " file.py | 10 +++---"
    stat_re = re.compile(r"^\s*(.+?)\s+\|\s+(\d+)\s+([+\-]+)$")
    summary_re = re.compile(r"^\s*(\d+) files? changed(?:,\s+(\d+) insertions?\(\+\))?(?:,\s+(\d+) deletions?\(\-\))?")  
    
    # Try --stat format first
    stat_files: list[str] = []
    stat_summary = ""
    for line in lines:
        sm = summary_re.match(line.strip())
        if sm:
            stat_summary = line.strip()
            continue
        m = stat_re.match(line)
        if m:
            fname = m.group(1).strip()
            count = m.group(2)
            bar = m.group(3)
            plus = bar.count("+")
            minus = bar.count("-")
            stat_files.append(f"{fname}  +{plus} -{minus}")

    if stat_files:
        header = stat_summary or f"{len(stat_files)} files changed"
        return header + "\n" + "\n".join(stat_files)

    # Full diff format: diff --git a/file b/file
    files: list[str] = []
    current_file = ""
    additions = 0
    deletions = 0

    for line in lines:
        if line.startswith("diff --git"):
            if current_file:
                files.append(f"{current_file}  +{additions} -{deletions}")
            parts = line.split()
            current_file = parts[-1].lstrip("b/") if parts else "?"
            additions = 0
            deletions = 0
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
        elif line.startswith("index ") or line.startswith("---") or line.startswith("+++"):
            continue

    if current_file:
        files.append(f"{current_file}  +{additions} -{deletions}")

    if not files:
        return raw.strip()  # pass through if no diff detected

    total_add = sum(int(f.split("+")[1].split()[0]) for f in files)
    total_del = sum(int(f.split("-")[-1]) for f in files)
    summary = f"{len(files)} files changed, +{total_add} -{total_del}"

    return summary + "\n" + "\n".join(files)


def compress_git_push(raw: str) -> str:
    """Push output → 'ok <branch>'."""
    # Extract branch name
    branch_match = re.search(r"(\S+)\s*->\s*(\S+)", raw)
    if branch_match:
        return f"ok {branch_match.group(2)}"
    if "Everything up-to-date" in raw:
        return "ok (up-to-date)"
    return raw.strip().split("\n")[-1] if raw.strip() else "ok"


# ---------------------------------------------------------------------------
# Directory listing compressor
# ---------------------------------------------------------------------------

def compress_ls(raw: str) -> str:
    """Compact directory listing — group by type, skip noise."""
    lines = raw.strip().split("\n")
    # Filter out total line and permission details
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("total "):
            continue
        # If it looks like ls -l output (starts with drwx or -rw-)
        if re.match(r"^[d\-rwxlst]{10}", stripped):
            # Extract just the filename (last token)
            parts = stripped.split()
            if parts:
                name = parts[-1]
                if stripped.startswith("d"):
                    name += "/"
                cleaned.append(name)
        else:
            cleaned.append(stripped)

    return group_by_directory(cleaned)


# ---------------------------------------------------------------------------
# Grep/search compressor
# ---------------------------------------------------------------------------

def compress_grep(raw: str) -> str:
    """Group grep results by file."""
    from collections import defaultdict
    lines = raw.strip().split("\n")
    by_file: dict[str, list[str]] = defaultdict(list)
    other: list[str] = []

    for line in lines:
        # Pattern: file:line:content or file:content
        match = re.match(r"^([^:]+):(\d+:)?\s*(.*)$", line)
        if match:
            filepath = match.group(1)
            content = match.group(3).strip()
            line_num = match.group(2).rstrip(":") if match.group(2) else ""
            if line_num:
                by_file[filepath].append(f"L{line_num}: {content}")
            else:
                by_file[filepath].append(content)
        else:
            other.append(line)

    parts: list[str] = []
    for filepath, matches in sorted(by_file.items()):
        parts.append(f"{filepath} ({len(matches)} matches)")
        for m in matches[:10]:
            parts.append(f"  {m}")
        if len(matches) > 10:
            parts.append(f"  ... +{len(matches) - 10} more")

    parts.extend(other)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Test runner compressor
# ---------------------------------------------------------------------------

def compress_test_output(raw: str) -> str:
    """Show only failures + summary for test runners (pytest, cargo test, etc.).
    
    Extracts:
    - FAILED test names
    - Error/assertion messages
    - Final summary line (e.g. '24 passed, 1 failed')
    Discards: all PASSED test lines, session info, separators.
    """
    lines = raw.strip().split("\n")
    failed_tests: list[str] = []
    failure_details: list[str] = []
    summary_line = ""
    in_failure_block = False

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        # Final summary (pytest: "X passed, Y failed in Zs")
        if re.search(r"\d+\s+(passed|failed).*in\s+[\d.]+s", lower):
            summary_line = stripped
            continue
        # cargo test summary ("test result: ...")
        if lower.startswith("test result:"):
            summary_line = stripped
            continue

        # FAILED test name lines
        if "FAILED" in stripped and "::" in stripped:
            failed_tests.append(stripped)
            continue

        # Start of failure detail block (pytest style)
        if stripped.startswith("______") or stripped.startswith("FAILURES"):
            in_failure_block = True
            continue

        # End of failure detail block
        if in_failure_block and (stripped.startswith("====") or stripped.startswith("----")):
            in_failure_block = False
            continue

        # Capture failure block content
        if in_failure_block and stripped:
            # Skip the test function def line, keep assertion errors
            if stripped.startswith("E ") or "Error" in stripped or "assert" in lower:
                failure_details.append(stripped)
            elif stripped.startswith(">"):
                failure_details.append(stripped)
            # Also capture file:line references
            elif re.match(r"^\S+\.py:\d+:", stripped):
                failure_details.append(stripped)

        # Skip PASSED lines entirely
        if "PASSED" in stripped or "passed" in stripped:
            continue

    parts: list[str] = []
    if failed_tests:
        parts.append(f"FAILED ({len(failed_tests)}):")
        for ft in failed_tests[:20]:
            parts.append(f"  {ft}")
    if failure_details:
        parts.append("")
        parts.append("DETAILS:")
        for fd in failure_details[:20]:
            parts.append(f"  {fd}")
    if summary_line:
        parts.append("")
        parts.append(summary_line)
    elif not failed_tests:
        parts.append("ALL TESTS PASSED")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Generic compressor pipeline
# ---------------------------------------------------------------------------

def compress_output(
    raw: str,
    command_type: str = "generic",
    max_lines: int = 80,
) -> CompressionResult:
    """Apply compression strategies based on command type.

    Supported command_type values:
    - "git_status", "git_log", "git_diff", "git_push"
    - "ls", "tree"
    - "grep", "search", "rg"
    - "test", "pytest", "cargo_test", "npm_test"
    - "generic" (default — applies all 4 strategies)
    """
    original_tokens = _estimate_tokens(raw)
    strategies: list[str] = []

    # 1. Always apply smart filtering first
    filtered, filter_strategies = smart_filter(raw)
    strategies.extend(filter_strategies)

    # 2. Apply command-specific compression
    ctype = command_type.lower().replace(" ", "_").replace("-", "_")

    if ctype == "git_status":
        compressed = compress_git_status(filtered)
        strategies.append("git_status_compact")
    elif ctype == "git_log":
        compressed = compress_git_log(filtered)
        strategies.append("git_log_oneline")
    elif ctype == "git_diff":
        compressed = compress_git_diff(filtered)
        strategies.append("git_diff_summary")
    elif ctype in ("git_push", "git_pull", "git_add", "git_commit"):
        compressed = compress_git_push(filtered)
        strategies.append("git_action_compact")
    elif ctype in ("ls", "tree", "dir"):
        compressed = compress_ls(filtered)
        strategies.append("ls_grouped")
    elif ctype in ("grep", "search", "rg", "findstr"):
        compressed = compress_grep(filtered)
        strategies.append("grep_grouped")
    elif ctype in ("test", "pytest", "cargo_test", "npm_test", "go_test", "vitest"):
        compressed = compress_test_output(filtered)
        strategies.append("test_failures_only")
    else:
        # Generic pipeline: dedup → truncate
        compressed = filtered
        deduped, dedup_count = deduplicate_lines(compressed)
        if dedup_count > 0:
            compressed = deduped
            strategies.append(f"dedup({dedup_count} lines)")

    # 3. Truncation (always for long output)
    compressed, was_truncated = truncate_output(compressed, max_lines=max_lines)
    if was_truncated:
        strategies.append("truncated")

    compressed_tokens = _estimate_tokens(compressed)
    savings = (1 - compressed_tokens / max(original_tokens, 1)) * 100

    return CompressionResult(
        original=raw,
        compressed=compressed,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        savings_pct=max(0.0, savings),
        strategy_applied=strategies,
    )


# ---------------------------------------------------------------------------
# Auto-detect command type from command string
# ---------------------------------------------------------------------------

_COMMAND_TYPE_MAP: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bgit\s+status\b"), "git_status"),
    (re.compile(r"\bgit\s+log\b"), "git_log"),
    (re.compile(r"\bgit\s+diff\b"), "git_diff"),
    (re.compile(r"\bgit\s+push\b"), "git_push"),
    (re.compile(r"\bgit\s+pull\b"), "git_pull"),
    (re.compile(r"\bgit\s+add\b"), "git_add"),
    (re.compile(r"\bgit\s+commit\b"), "git_commit"),
    (re.compile(r"\b(ls|dir|Get-ChildItem)\b"), "ls"),
    (re.compile(r"\btree\b"), "tree"),
    (re.compile(r"\b(grep|rg|findstr|Select-String)\b"), "grep"),
    (re.compile(r"\bpytest\b"), "pytest"),
    (re.compile(r"\bcargo\s+test\b"), "cargo_test"),
    (re.compile(r"\bnpm\s+(test|run\s+test)\b"), "npm_test"),
    (re.compile(r"\bgo\s+test\b"), "go_test"),
    (re.compile(r"\bvitest\b"), "vitest"),
]


def detect_command_type(command: str) -> str:
    """Auto-detect command type from the command string."""
    for pattern, ctype in _COMMAND_TYPE_MAP:
        if pattern.search(command):
            return ctype
    return "generic"
