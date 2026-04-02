"""Output compressor for CLI commands — RTK-equivalent token savings.

Applies four compression strategies per command type:
1. Smart Filtering — removes noise (comments, whitespace, boilerplate)
2. Grouping — aggregates similar items (files by dir, errors by type)
3. Truncation — keeps relevant context, cuts redundancy
4. Deduplication — collapses repeated lines with counts
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class CompressionResult:
    """Result of compressing CLI output."""
    original: str
    compressed: str
    original_chars: int
    compressed_chars: int
    original_lines: int
    compressed_lines: int
    savings_pct: float
    command_type: str
    strategies_applied: list[str] = field(default_factory=list)

    @property
    def original_tokens_est(self) -> int:
        return max(1, self.original_chars // 4)

    @property
    def compressed_tokens_est(self) -> int:
        return max(1, self.compressed_chars // 4)


def deduplicate_lines(text: str, threshold: int = 2) -> str:
    """Collapse consecutive or scattered duplicate lines with counts."""
    lines = text.splitlines()
    if len(lines) <= 3:
        return text
    counts: Counter[str] = Counter()
    seen_order: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        counts[stripped] += 1
        if stripped not in seen_order:
            seen_order.append(stripped)
    result: list[str] = []
    for line in seen_order:
        count = counts[line]
        if count >= threshold:
            result.append(f"{line}  (x{count})")
        else:
            result.append(line)
    return "\n".join(result)


def strip_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)


def truncate_lines(text: str, max_lines: int = 200, tail: int = 20) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    head = lines[: max_lines - tail]
    foot = lines[-tail:]
    omitted = len(lines) - (max_lines - tail) - tail
    return "\n".join(head + [f"\n... ({omitted} lines omitted) ...\n"] + foot)


def remove_progress_bars(text: str) -> str:
    patterns = [
        r"^.*\d+%\|[#=\-\s]+\|.*$",
        r"^.*\[[-=#>\s]+\]\s*\d+%.*$",
        r"^.*downloading.*\d+(\.\d+)?\s*(MB|KB|GB|B)/s.*$",
        r"^Resolving\s+.*done\.?$",
        r"^Connecting\s+.*connected\.?$",
        r"^(Receiving|Counting|Compressing)\s+objects:\s+\d+%.*$",
        r"^\s*%\s+Total\s+%\s+Received.*$",
    ]
    combined = re.compile("|".join(patterns), re.MULTILINE | re.IGNORECASE)
    return combined.sub("", text)


def _compress_git_status(output: str) -> tuple[str, list[str]]:
    lines = output.splitlines()
    strategies = ["filter", "group"]
    result: list[str] = []
    branch = ""
    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []
    section = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("On branch"):
            branch = stripped.replace("On branch ", "")
            continue
        if stripped.startswith("Your branch is"):
            result.append(stripped)
            continue
        if "Changes to be committed" in stripped:
            section = "staged"
            continue
        if "Changes not staged" in stripped:
            section = "unstaged"
            continue
        if "Untracked files:" in stripped:
            section = "untracked"
            continue
        if stripped.startswith("(use "):
            continue
        if "no changes added" in stripped:
            continue
        if "nothing to commit" in stripped:
            result.append(stripped)
            continue
        if section == "staged":
            staged.append(stripped)
        elif section == "unstaged":
            unstaged.append(stripped)
        elif section == "untracked":
            untracked.append(stripped)
    parts: list[str] = []
    if branch:
        parts.append(f"branch: {branch}")
    parts.extend(result)
    if staged:
        parts.append(f"staged ({len(staged)}):")
        parts.extend(f"  {s}" for s in staged)
    if unstaged:
        parts.append(f"unstaged ({len(unstaged)}):")
        parts.extend(f"  {s}" for s in unstaged)
    if untracked:
        parts.append(f"untracked ({len(untracked)}):")
        parts.extend(f"  {s}" for s in untracked)
    if not staged and not unstaged and not untracked and not result:
        parts.append("clean")
    return "\n".join(parts), strategies


def _compress_git_log(output: str) -> tuple[str, list[str]]:
    strategies = ["filter", "truncate"]
    lines = output.splitlines()
    commits: list[str] = []
    current_hash = ""
    current_msg = ""
    current_date = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("commit "):
            if current_hash and current_msg:
                commits.append(f"{current_hash[:7]} {current_date} {current_msg}")
            current_hash = stripped.replace("commit ", "").strip()
            current_msg = ""
            current_date = ""
        elif stripped.startswith("Author:"):
            continue
        elif stripped.startswith("Date:"):
            current_date = stripped.replace("Date:", "").strip()
            parts = current_date.split()
            if len(parts) >= 4:
                current_date = " ".join(parts[:3])
        elif stripped.startswith("Merge:"):
            continue
        else:
            if not current_msg:
                current_msg = stripped
    if current_hash and current_msg:
        commits.append(f"{current_hash[:7]} {current_date} {current_msg}")
    if not commits:
        return truncate_lines(output, max_lines=30), strategies
    return "\n".join(commits[:50]), strategies


def _compress_git_diff(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    lines = output.splitlines()
    result: list[str] = []
    skip_prefixes = ("index ", "old mode", "new mode", "similarity index",
                     "rename from", "rename to", "copy from", "copy to")
    for line in lines:
        if any(line.startswith(p) for p in skip_prefixes):
            continue
        result.append(line)
    text = "\n".join(result)
    return truncate_lines(text, max_lines=300, tail=30), strategies


def _compress_git_push_pull(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    output_clean = strip_ansi(output)
    branch_match = re.search(r"(\S+)\s*->\s*(\S+)", output_clean)
    rejection = "rejected" in output_clean.lower() or "error" in output_clean.lower()
    if rejection:
        return output_clean.strip(), strategies
    if "Everything up-to-date" in output_clean:
        return "ok (up-to-date)", strategies
    if branch_match:
        return f"ok {branch_match.group(2)}", strategies
    file_changes = re.search(r"(\d+)\s+files?\s+changed", output_clean)
    insertions = re.search(r"(\d+)\s+insertions?", output_clean)
    deletions = re.search(r"(\d+)\s+deletions?", output_clean)
    if file_changes:
        files = file_changes.group(1)
        ins = insertions.group(1) if insertions else "0"
        dels = deletions.group(1) if deletions else "0"
        return f"ok {files} files +{ins} -{dels}", strategies
    if "Already up to date" in output_clean:
        return "ok (up-to-date)", strategies
    noise = [r"^Enumerating objects:.*$", r"^Counting objects:.*$",
             r"^Compressing objects:.*$", r"^Writing objects:.*$",
             r"^Delta compression.*$", r"^remote:.*$",
             r"^Total \d+.*$", r"^Unpacking objects:.*$"]
    combined = re.compile("|".join(noise), re.MULTILINE)
    cleaned = combined.sub("", output_clean).strip()
    cleaned = strip_blank_lines(cleaned)
    return cleaned if cleaned else "ok", strategies


def _compress_git_add(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = output.strip()
    if not clean:
        return "ok", strategies
    if "fatal:" in clean or "error:" in clean:
        return clean, strategies
    return "ok", strategies


def _compress_git_commit(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = strip_ansi(output).strip()
    match = re.search(r"\[(\S+)\s+([a-f0-9]{7,})\]", clean)
    if match:
        return f"ok {match.group(2)}", strategies
    if "nothing to commit" in clean:
        return "nothing to commit", strategies
    return clean, strategies


def _compress_ls_tree(output: str) -> tuple[str, list[str]]:
    strategies = ["filter", "group"]
    lines = output.splitlines()
    if len(lines) <= 10:
        return output, strategies
    compact_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^[drwx\-lsStT]{10}\s+\d+\s+\S+\s+\S+\s+[\d,]+\s+\w+\s+\d+\s+[\d:]+\s+(.+)$", stripped)
        if match:
            name = match.group(1)
            if stripped.startswith("d"):
                compact_lines.append(f"  {name}/")
            else:
                compact_lines.append(f"  {name}")
        else:
            compact_lines.append(stripped)
    return truncate_lines("\n".join(compact_lines), max_lines=60), strategies


def _compress_cat_read(output: str) -> tuple[str, list[str]]:
    strategies = ["filter", "truncate"]
    text = strip_blank_lines(output)
    text = re.sub(r"(^[ \t]*(?:#|//|/\*|\*)[^\n]*\n){4,}",
                  lambda m: f"  # ... ({m.group().count(chr(10))} comment lines) ...\n",
                  text, flags=re.MULTILINE)
    return truncate_lines(text, max_lines=200, tail=30), strategies


def _compress_grep_rg(output: str) -> tuple[str, list[str]]:
    strategies = ["group", "truncate"]
    lines = output.splitlines()
    if len(lines) <= 10:
        return output, strategies
    by_file: dict[str, list[str]] = {}
    other: list[str] = []
    for line in lines:
        match = re.match(r"^([^:]+):(\d+):(.*)$", line)
        if match:
            fname = match.group(1)
            rest = f"  L{match.group(2)}: {match.group(3).strip()}"
            by_file.setdefault(fname, []).append(rest)
        else:
            other.append(line)
    if not by_file:
        return truncate_lines(output, max_lines=100), strategies
    result: list[str] = []
    for fname, matches in by_file.items():
        result.append(f"{fname} ({len(matches)} matches):")
        for m in matches[:10]:
            result.append(m)
        if len(matches) > 10:
            result.append(f"  ... +{len(matches) - 10} more")
    if other:
        result.extend(other[:5])
    return truncate_lines("\n".join(result), max_lines=150), strategies


def _compress_find(output: str) -> tuple[str, list[str]]:
    strategies = ["group", "truncate"]
    lines = output.splitlines()
    if len(lines) <= 15:
        return output, strategies
    by_dir: dict[str, list[str]] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        normalized = stripped.replace("\\\\", "/")
        parts = normalized.rsplit("/", 1)
        if len(parts) == 2:
            d, f = parts
            by_dir.setdefault(d, []).append(f)
        else:
            by_dir.setdefault(".", []).append(stripped)
    result: list[str] = []
    for d, files in sorted(by_dir.items()):
        result.append(f"{d}/ ({len(files)} files)")
        for f in files[:5]:
            result.append(f"  {f}")
        if len(files) > 5:
            result.append(f"  ... +{len(files) - 5} more")
    return truncate_lines("\n".join(result), max_lines=100), strategies


def _compress_diff(output: str) -> tuple[str, list[str]]:
    return _compress_git_diff(output)


def _compress_test_output(output: str, runner: str = "generic") -> tuple[str, list[str]]:
    strategies = ["filter", "group"]
    clean = strip_ansi(output)
    lines = clean.splitlines()
    summary_patterns = [
        r"(\d+\s+passed.*\d+\s+failed)", r"(FAILED.*tests?)",
        r"(Tests?:\s+\d+.*)", r"(test result:.*)",
        r"(\d+ tests?, \d+ assertions?.*)", r"(=+\s+\d+\s+(passed|failed).*=+)",
        r"(ok\.\s+\d+\s+passed.*)", r"(FAIL[ED]*\s*[:\-]?\s*\d+)",
    ]
    summary = ""
    for pat in summary_patterns:
        m = re.search(pat, clean, re.IGNORECASE)
        if m:
            summary = m.group(0).strip()
            break
    has_failure = any(kw in clean.lower() for kw in ["fail", "error", "panic", "assertion", "traceback"])
    if not has_failure:
        if summary:
            return f"PASSED: {summary}", strategies
        test_count = sum(1 for ln in lines if re.search(r"test.*ok|pass", ln, re.IGNORECASE))
        if test_count > 0:
            return f"PASSED: {test_count} tests", strategies
        return truncate_lines(clean, max_lines=30), strategies
    failure_sections: list[str] = []
    in_failure = False
    failure_buffer: list[str] = []
    failure_start = re.compile(r"(FAIL|FAILED|ERROR|panic|assertion|Traceback|thread .* panicked)", re.IGNORECASE)
    for line in lines:
        if failure_start.search(line):
            in_failure = True
        if in_failure:
            failure_buffer.append(line)
            if (not line.strip() and len(failure_buffer) > 3) or line.strip().startswith("---"):
                failure_sections.append("\n".join(failure_buffer))
                failure_buffer = []
                in_failure = False
    if failure_buffer:
        failure_sections.append("\n".join(failure_buffer))
    result_parts: list[str] = []
    if summary:
        result_parts.append(summary)
    else:
        result_parts.append(f"FAILED ({len(failure_sections)} failure sections)")
    for section in failure_sections[:10]:
        result_parts.append(truncate_lines(section, max_lines=20, tail=5))
    if len(failure_sections) > 10:
        result_parts.append(f"\n... +{len(failure_sections) - 10} more failures")
    return "\n\n".join(result_parts), strategies


def _compress_cargo_test(output: str) -> tuple[str, list[str]]:
    return _compress_test_output(output, "cargo")

def _compress_npm_test(output: str) -> tuple[str, list[str]]:
    return _compress_test_output(output, "npm")

def _compress_pytest(output: str) -> tuple[str, list[str]]:
    return _compress_test_output(output, "pytest")

def _compress_vitest(output: str) -> tuple[str, list[str]]:
    return _compress_test_output(output, "vitest")

def _compress_playwright(output: str) -> tuple[str, list[str]]:
    return _compress_test_output(output, "playwright")

def _compress_go_test(output: str) -> tuple[str, list[str]]:
    return _compress_test_output(output, "go")


def _compress_build_lint(output: str, tool_name: str = "generic") -> tuple[str, list[str]]:
    strategies = ["filter", "group"]
    clean = strip_ansi(output)
    noise_patterns = [
        r"^npm\s+(warn|notice).*$", r"^>\s+\S+@\S+\s+\S+$",
        r"^\s*Compiling\s+\S+\s+v\S+.*$", r"^\s*Downloading\s+\S+\s+v\S+.*$",
        r"^\s*Downloaded\s+\d+\s+crates.*$", r"^\s*Finished\s+.*$",
        r"^\s*Fresh\s+\S+\s+v\S+.*$", r"^go:\s+downloading\s+.*$",
    ]
    combined = re.compile("|".join(noise_patterns), re.MULTILINE)
    clean = combined.sub("", clean)
    clean = strip_blank_lines(clean)
    errors: dict[str, list[str]] = {}
    warnings: dict[str, list[str]] = {}
    other_lines: list[str] = []
    for line in clean.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = re.match(r"^(.+?):(\d+):(\d+)?:?\s*(error|warning|Error|Warning)[:\s]+(.*)$", stripped)
        if m:
            fname, lineno, _, severity, msg = m.groups()
            entry = f"  L{lineno}: {msg.strip()}"
            if "error" in severity.lower():
                errors.setdefault(fname, []).append(entry)
            else:
                warnings.setdefault(fname, []).append(entry)
        else:
            other_lines.append(stripped)
    if not errors and not warnings:
        return truncate_lines(clean, max_lines=100), strategies
    result: list[str] = []
    if errors:
        total_errs = sum(len(v) for v in errors.values())
        result.append(f"ERRORS ({total_errs}):")
        for fname, errs in errors.items():
            result.append(f"  {fname} ({len(errs)}):")
            for e in errs[:15]:
                result.append(f"    {e}")
            if len(errs) > 15:
                result.append(f"    ... +{len(errs) - 15} more")
    if warnings:
        total_warns = sum(len(v) for v in warnings.values())
        result.append(f"WARNINGS ({total_warns}):")
        for fname, warns in warnings.items():
            result.append(f"  {fname} ({len(warns)}):")
            for w in warns[:10]:
                result.append(f"    {w}")
            if len(warns) > 10:
                result.append(f"    ... +{len(warns) - 10} more")
    for line in other_lines[-5:]:
        result.append(line)
    return "\n".join(result), strategies


def _compress_eslint(o: str) -> tuple[str, list[str]]:
    return _compress_build_lint(o, "eslint")

def _compress_tsc(o: str) -> tuple[str, list[str]]:
    return _compress_build_lint(o, "tsc")

def _compress_next_build(o: str) -> tuple[str, list[str]]:
    return _compress_build_lint(o, "next")

def _compress_cargo_build(o: str) -> tuple[str, list[str]]:
    return _compress_build_lint(o, "cargo")

def _compress_cargo_clippy(o: str) -> tuple[str, list[str]]:
    return _compress_build_lint(o, "clippy")

def _compress_ruff(o: str) -> tuple[str, list[str]]:
    return _compress_build_lint(o, "ruff")

def _compress_golangci_lint(o: str) -> tuple[str, list[str]]:
    return _compress_build_lint(o, "golangci-lint")


def _compress_prettier(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = strip_ansi(output)
    lines = [l.strip() for l in clean.splitlines() if l.strip()]
    files = [l for l in lines if not l.startswith("Checking") and not l.startswith("All matched")]
    if any("All matched" in l for l in lines):
        return "ok (all formatted)", strategies
    if files:
        return f"Needs formatting ({len(files)} files):\n" + "\n".join(f"  {f}" for f in files[:30]), strategies
    return clean, strategies


def _compress_pip_list(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = strip_ansi(output)
    packages: list[str] = []
    for line in clean.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("-") or stripped.startswith("Package"):
            continue
        parts = stripped.split()
        if len(parts) >= 2:
            packages.append(f"{parts[0]}=={parts[1]}")
        else:
            packages.append(stripped)
    return f"{len(packages)} packages:\n" + "\n".join(packages), strategies


def _compress_pip_outdated(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = strip_ansi(output)
    packages: list[str] = []
    for line in clean.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("-") or stripped.startswith("Package"):
            continue
        parts = stripped.split()
        if len(parts) >= 3:
            packages.append(f"{parts[0]}: {parts[1]} -> {parts[2]}")
    if not packages:
        return "all up to date", strategies
    return f"{len(packages)} outdated:\n" + "\n".join(packages), strategies


def _compress_pnpm_list(output: str) -> tuple[str, list[str]]:
    strategies = ["filter", "truncate"]
    clean = strip_ansi(output)
    return truncate_lines(strip_blank_lines(clean), max_lines=60), strategies


def _compress_prisma_generate(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = strip_ansi(output)
    lines = [line.strip() for line in clean.splitlines() if line.strip() and not re.match(r"^[\s\u2502\u250c\u2510\u2514\u2518\u2500\u251c\u2524\u252c\u2534\u253c]+$", line)]
    return "\n".join(lines) if lines else "ok", strategies


def _compress_docker_ps(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = strip_ansi(output)
    lines = clean.splitlines()
    if len(lines) <= 1:
        return clean, strategies
    containers = [l.strip() for l in lines[1:] if l.strip()]
    result = f"{len(containers)} containers:\n" + "\n".join(f"  {c}" for c in containers)
    return result, strategies


def _compress_docker_images(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = strip_ansi(output)
    lines = clean.splitlines()
    if len(lines) <= 1:
        return clean, strategies
    images: list[str] = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 3:
            images.append(f"{parts[0]}:{parts[1]} ({parts[-1]})")
    return f"{len(images)} images:\n" + "\n".join(f"  {i}" for i in images), strategies


def _compress_docker_logs(output: str) -> tuple[str, list[str]]:
    strategies = ["dedup", "truncate"]
    clean = strip_ansi(output)
    deduped = deduplicate_lines(clean)
    return truncate_lines(deduped, max_lines=100), strategies


def _compress_docker_compose_ps(o: str) -> tuple[str, list[str]]:
    return _compress_docker_ps(o)


def _compress_kubectl_pods(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = strip_ansi(output)
    lines = clean.splitlines()
    if len(lines) <= 1:
        return clean, strategies
    pods: list[str] = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 3:
            name, ready, status = parts[0], parts[1], parts[2]
            restarts = parts[3] if len(parts) > 3 else ""
            pods.append(f"{name} {status} ready={ready} restarts={restarts}")
    return f"{len(pods)} pods:\n" + "\n".join(f"  {p}" for p in pods), strategies


def _compress_kubectl_logs(o: str) -> tuple[str, list[str]]:
    return _compress_docker_logs(o)


def _compress_kubectl_services(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = strip_ansi(output)
    lines = clean.splitlines()
    if len(lines) <= 1:
        return clean, strategies
    svcs: list[str] = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 4:
            svcs.append(f"{parts[0]} type={parts[1]} ip={parts[2]} ports={parts[3]}")
    return f"{len(svcs)} services:\n" + "\n".join(f"  {s}" for s in svcs), strategies


def _extract_json_schema(data: Any, depth: int = 0, max_depth: int = 4) -> Any:
    if depth >= max_depth:
        return f"<{type(data).__name__}>"
    if isinstance(data, dict):
        return {k: _extract_json_schema(v, depth + 1, max_depth) for k, v in list(data.items())[:20]}
    if isinstance(data, list):
        if not data:
            return []
        return [_extract_json_schema(data[0], depth + 1, max_depth), f"... ({len(data)} items)"]
    return f"<{type(data).__name__}>"


def _compress_curl_wget(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    clean = strip_ansi(output)
    clean = remove_progress_bars(clean)
    clean = strip_blank_lines(clean)
    import json as json_mod
    try:
        data = json_mod.loads(clean)
        schema = _extract_json_schema(data, max_depth=3)
        return "JSON response:\n" + json_mod.dumps(schema, indent=2, ensure_ascii=False), strategies + ["schema"]
    except (json_mod.JSONDecodeError, ValueError):
        pass
    return truncate_lines(clean, max_lines=100), strategies


def _compress_gh_pr_list(output: str) -> tuple[str, list[str]]:
    strategies = ["filter"]
    return strip_blank_lines(strip_ansi(output)), strategies

def _compress_gh_pr_view(output: str) -> tuple[str, list[str]]:
    strategies = ["filter", "truncate"]
    return truncate_lines(strip_blank_lines(strip_ansi(output)), max_lines=60), strategies

def _compress_gh_issue_list(o: str) -> tuple[str, list[str]]:
    return _compress_gh_pr_list(o)

def _compress_gh_run_list(o: str) -> tuple[str, list[str]]:
    return _compress_gh_pr_list(o)


def _passthrough(output: str) -> tuple[str, list[str]]:
    clean = strip_ansi(output)
    return strip_blank_lines(clean), ["passthrough"]


COMMAND_PROFILES: list[tuple[re.Pattern[str], Callable[[str], tuple[str, list[str]]]]] = [
    (re.compile(r"\bgit\s+status\b", re.I), _compress_git_status),
    (re.compile(r"\bgit\s+log\b", re.I), _compress_git_log),
    (re.compile(r"\bgit\s+diff\b", re.I), _compress_git_diff),
    (re.compile(r"\bgit\s+(push|pull|fetch)\b", re.I), _compress_git_push_pull),
    (re.compile(r"\bgit\s+add\b", re.I), _compress_git_add),
    (re.compile(r"\bgit\s+commit\b", re.I), _compress_git_commit),
    (re.compile(r"\bgh\s+pr\s+list\b", re.I), _compress_gh_pr_list),
    (re.compile(r"\bgh\s+pr\s+view\b", re.I), _compress_gh_pr_view),
    (re.compile(r"\bgh\s+issue\s+list\b", re.I), _compress_gh_issue_list),
    (re.compile(r"\bgh\s+run\s+list\b", re.I), _compress_gh_run_list),
    (re.compile(r"\bcargo\s+test\b", re.I), _compress_cargo_test),
    (re.compile(r"\bnpm\s+(test|run\s+test)\b", re.I), _compress_npm_test),
    (re.compile(r"\bpytest\b", re.I), _compress_pytest),
    (re.compile(r"\bvitest\b", re.I), _compress_vitest),
    (re.compile(r"\bplaywright\b", re.I), _compress_playwright),
    (re.compile(r"\bgo\s+test\b", re.I), _compress_go_test),
    (re.compile(r"\beslint\b", re.I), _compress_eslint),
    (re.compile(r"\bbiome\b", re.I), _compress_eslint),
    (re.compile(r"\btsc\b", re.I), _compress_tsc),
    (re.compile(r"\bnext\s+build\b", re.I), _compress_next_build),
    (re.compile(r"\bprettier\b", re.I), _compress_prettier),
    (re.compile(r"\bcargo\s+build\b", re.I), _compress_cargo_build),
    (re.compile(r"\bcargo\s+clippy\b", re.I), _compress_cargo_clippy),
    (re.compile(r"\bruff\s+(check|format)\b", re.I), _compress_ruff),
    (re.compile(r"\bgolangci-lint\b", re.I), _compress_golangci_lint),
    (re.compile(r"\bpip\s+(list\s+--outdated|outdated)\b", re.I), _compress_pip_outdated),
    (re.compile(r"\bpip\s+list\b", re.I), _compress_pip_list),
    (re.compile(r"\bpnpm\s+list\b", re.I), _compress_pnpm_list),
    (re.compile(r"\bprisma\s+generate\b", re.I), _compress_prisma_generate),
    (re.compile(r"\bdocker\s+ps\b", re.I), _compress_docker_ps),
    (re.compile(r"\bdocker\s+images?\b", re.I), _compress_docker_images),
    (re.compile(r"\bdocker\s+logs?\b", re.I), _compress_docker_logs),
    (re.compile(r"\bdocker[\s-]+compose\s+ps\b", re.I), _compress_docker_compose_ps),
    (re.compile(r"\bkubectl\s+(get\s+)?pods?\b", re.I), _compress_kubectl_pods),
    (re.compile(r"\bkubectl\s+logs?\b", re.I), _compress_kubectl_logs),
    (re.compile(r"\bkubectl\s+(get\s+)?services?\b", re.I), _compress_kubectl_services),
    (re.compile(r"\bcurl\s+", re.I), _compress_curl_wget),
    (re.compile(r"\bwget\s+", re.I), _compress_curl_wget),
    (re.compile(r"\b(ls|dir|tree|Get-ChildItem|gci)\b", re.I), _compress_ls_tree),
    (re.compile(r"\b(cat|head|tail|type|Get-Content|gc)\b", re.I), _compress_cat_read),
    (re.compile(r"\b(grep|rg|ripgrep|findstr|Select-String)\b", re.I), _compress_grep_rg),
    (re.compile(r"\bfind\s+", re.I), _compress_find),
    (re.compile(r"\bdiff\s+", re.I), _compress_diff),
]


def detect_command_type(command: str) -> str:
    for pattern, _ in COMMAND_PROFILES:
        if pattern.search(command):
            return pattern.pattern.replace(r"\b", "").replace(r"\s+", " ").strip("()|")
    return "unknown"


def compress_output(command: str, raw_output: str) -> CompressionResult:
    if not raw_output or not raw_output.strip():
        return CompressionResult(
            original=raw_output or "", compressed=raw_output or "",
            original_chars=0, compressed_chars=0,
            original_lines=0, compressed_lines=0,
            savings_pct=0.0, command_type="empty",
            strategies_applied=["none"],
        )
    cleaned = strip_ansi(raw_output)
    compressor = _passthrough
    cmd_type = "unknown"
    for pattern, func in COMMAND_PROFILES:
        if pattern.search(command):
            compressor = func
            cmd_type = detect_command_type(command)
            break
    compressed, strategies = compressor(cleaned)
    compressed = strip_blank_lines(compressed)
    orig_chars = len(raw_output)
    comp_chars = len(compressed)
    savings = round((1 - comp_chars / max(1, orig_chars)) * 100, 1) if orig_chars > 0 else 0.0
    return CompressionResult(
        original=raw_output, compressed=compressed,
        original_chars=orig_chars, compressed_chars=comp_chars,
        original_lines=len(raw_output.splitlines()),
        compressed_lines=len(compressed.splitlines()),
        savings_pct=max(0.0, savings), command_type=cmd_type,
        strategies_applied=strategies,
    )
