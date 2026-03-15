"""PowerShell syntax fixer — auto-correct common Bash→PS mistakes.

Two-level approach:
- AUTO-FIX (12 patterns): safe transformations applied automatically
- DETECT-WARN (5 patterns): context-dependent, returned as warnings

Each fix is tagged with an ID (PS-01..PS-17) matching the error catalog.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FixResult:
    """Result of fixing a PowerShell command."""
    original: str
    fixed: str
    was_modified: bool
    fixes_applied: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "command": self.fixed,
            "was_modified": self.was_modified,
        }
        if self.fixes_applied:
            result["fixes_applied"] = self.fixes_applied
        if self.warnings:
            result["warnings"] = self.warnings
        return result


# ---------------------------------------------------------------------------
# PS-01: && → ;  (chain operator not supported in PS 5.1)
# ---------------------------------------------------------------------------
_AND_AND_RE = re.compile(r"\s*&&\s*")


def _fix_01_and_chain(cmd: str) -> tuple[str, str | None]:
    if "&&" in cmd:
        return _AND_AND_RE.sub(" ; ", cmd), "PS-01: replaced '&&' with ';' (PS 5.1 chain operator)"
    return cmd, None


# ---------------------------------------------------------------------------
# PS-02: < in unquoted strings → reserved redirection operator
# ---------------------------------------------------------------------------
# Only fix angle brackets that look like placeholders: <file>, <path>, <name>
_ANGLE_IN_HINT_RE = re.compile(r"<(\w+(?:\.\.\.?)?)>")


def _fix_02_angle_brackets(cmd: str) -> tuple[str, str | None]:
    if _ANGLE_IN_HINT_RE.search(cmd):
        fixed = _ANGLE_IN_HINT_RE.sub(r"[\1]", cmd)
        return fixed, "PS-02: replaced '<placeholder>' with '[placeholder]' to avoid redirect"
    return cmd, None


# ---------------------------------------------------------------------------
# PS-03: Unquoted paths with spaces
# ---------------------------------------------------------------------------
# Detect common patterns: cd C:\My Folder\sub  or  cat C:\path with space\file
_PATH_SPACE_RE = re.compile(
    r"(?:cd|pushd|Set-Location|cat|Get-Content|type|move|copy|del)\s+"
    r"([A-Za-z]:\\[^\";|&\n]+?\s+[^\";|&\n]+?)(?=\s*[;|&\n]|$)"
)


def _fix_03_unquoted_paths(cmd: str) -> tuple[str, str | None]:
    match = _PATH_SPACE_RE.search(cmd)
    if match:
        path = match.group(1).strip()
        # Only fix if path contains space and is not already quoted
        if " " in path and not path.startswith('"') and not path.startswith("'"):
            fixed = cmd[:match.start(1)] + f'"{path}"' + cmd[match.end(1):]
            return fixed, f'PS-03: quoted path with spaces: "{path}"'
    return cmd, None


# ---------------------------------------------------------------------------
# PS-04: Heredoc <<EOF → Detect only (complex to auto-fix)
# ---------------------------------------------------------------------------
_HEREDOC_RE = re.compile(r"<<\s*['\"]?(\w+)['\"]?")


def _detect_04_heredoc(cmd: str) -> str | None:
    if _HEREDOC_RE.search(cmd):
        return "PS-04: heredoc '<<EOF' not supported in PS. Use here-string: @\"\n...\n\"@"
    return None


# ---------------------------------------------------------------------------
# PS-05: export VAR=val → $env:VAR="val"
# ---------------------------------------------------------------------------
_EXPORT_RE = re.compile(r"\bexport\s+(\w+)=(.*?)(?=\s*[;&|]|$)")


def _fix_05_export(cmd: str) -> tuple[str, str | None]:
    match = _EXPORT_RE.search(cmd)
    if match:
        var = match.group(1)
        val = match.group(2).strip().strip('"').strip("'")
        replacement = f'$env:{var}="{val}"'
        fixed = cmd[:match.start()] + replacement + cmd[match.end():]
        return fixed, f"PS-05: 'export {var}={val}' → '{replacement}'"
    return cmd, None


# ---------------------------------------------------------------------------
# PS-06: $() subexpression in double quotes — Detect only
# ---------------------------------------------------------------------------
_SUBEXPR_RE = re.compile(r'"[^"]*\$\([^)]*\)[^"]*"')


def _detect_06_subexpression(cmd: str) -> str | None:
    if _SUBEXPR_RE.search(cmd):
        return "PS-06: $() subexpression in quotes works but errors inside propagate silently. Consider splitting."
    return None


# ---------------------------------------------------------------------------
# PS-07: grep → Select-String
# ---------------------------------------------------------------------------
_GREP_PIPE_RE = re.compile(r"\|\s*grep\s+")
_GREP_STANDALONE_RE = re.compile(r"^grep\s+", re.MULTILINE)


def _fix_07_grep(cmd: str) -> tuple[str, str | None]:
    fixed = cmd
    changed = False
    if _GREP_PIPE_RE.search(fixed):
        fixed = _GREP_PIPE_RE.sub("| Select-String ", fixed)
        changed = True
    if _GREP_STANDALONE_RE.search(fixed):
        fixed = _GREP_STANDALONE_RE.sub("Select-String ", fixed)
        changed = True
    if changed:
        return fixed, "PS-07: replaced 'grep' with 'Select-String'"
    return cmd, None


# ---------------------------------------------------------------------------
# PS-08: head/tail → Select-Object -First/-Last
# ---------------------------------------------------------------------------
_HEAD_RE = re.compile(r"\|\s*head\s+(?:-n?\s*)?(\d+)")
_TAIL_RE = re.compile(r"\|\s*tail\s+(?:-n?\s*)?(\d+)")
_WC_L_RE = re.compile(r"\|\s*wc\s+-l")


def _fix_08_head_tail(cmd: str) -> tuple[str, str | None]:
    fixed = cmd
    applied: list[str] = []

    m = _HEAD_RE.search(fixed)
    if m:
        n = m.group(1)
        fixed = fixed[:m.start()] + f"| Select-Object -First {n}" + fixed[m.end():]
        applied.append(f"head -{n} → Select-Object -First {n}")

    m = _TAIL_RE.search(fixed)
    if m:
        n = m.group(1)
        fixed = fixed[:m.start()] + f"| Select-Object -Last {n}" + fixed[m.end():]
        applied.append(f"tail -{n} → Select-Object -Last {n}")

    m = _WC_L_RE.search(fixed)
    if m:
        fixed = fixed[:m.start()] + "| Measure-Object -Line" + fixed[m.end():]
        applied.append("wc -l → Measure-Object -Line")

    if applied:
        return fixed, f"PS-08: {'; '.join(applied)}"
    return cmd, None


# ---------------------------------------------------------------------------
# PS-09: rm -rf → Remove-Item -Recurse -Force
# ---------------------------------------------------------------------------
_RM_RF_RE = re.compile(r"\brm\s+-(r|rf|fr)\s+")
_RM_R_RE = re.compile(r"\brm\s+-r\s+")
_MKDIR_P_RE = re.compile(r"\bmkdir\s+-p\s+")


def _fix_09_rm_rf(cmd: str) -> tuple[str, str | None]:
    fixed = cmd
    changed = False

    if _RM_RF_RE.search(fixed):
        fixed = _RM_RF_RE.sub("Remove-Item -Recurse -Force ", fixed)
        changed = True
    elif _RM_R_RE.search(fixed):
        fixed = _RM_R_RE.sub("Remove-Item -Recurse ", fixed)
        changed = True

    if _MKDIR_P_RE.search(fixed):
        fixed = _MKDIR_P_RE.sub("New-Item -ItemType Directory -Force -Path ", fixed)
        changed = True

    if changed:
        return fixed, "PS-09: replaced rm/mkdir Bash flags with PS equivalents"
    return cmd, None


# ---------------------------------------------------------------------------
# PS-10: ls -la → Get-ChildItem -Force
# ---------------------------------------------------------------------------
_LS_FLAGS_RE = re.compile(r"\bls\s+-(la|al|l|a|lah|lh)\b")


def _fix_10_ls_flags(cmd: str) -> tuple[str, str | None]:
    if _LS_FLAGS_RE.search(cmd):
        fixed = _LS_FLAGS_RE.sub("Get-ChildItem -Force", cmd)
        return fixed, "PS-10: replaced 'ls -la' with 'Get-ChildItem -Force'"
    return cmd, None


# ---------------------------------------------------------------------------
# PS-11: touch file → New-Item file
# ---------------------------------------------------------------------------
_TOUCH_RE = re.compile(r"\btouch\s+([^\s;|&]+)")


def _fix_11_touch(cmd: str) -> tuple[str, str | None]:
    match = _TOUCH_RE.search(cmd)
    if match:
        fname = match.group(1)
        replacement = f'New-Item -ItemType File -Force "{fname}"'
        fixed = cmd[:match.start()] + replacement + cmd[match.end():]
        return fixed, f"PS-11: 'touch {fname}' → 'New-Item ...'"
    return cmd, None


# ---------------------------------------------------------------------------
# PS-12: which → Get-Command
# ---------------------------------------------------------------------------
_WHICH_RE = re.compile(r"\bwhich\s+(\S+)")


def _fix_12_which(cmd: str) -> tuple[str, str | None]:
    match = _WHICH_RE.search(cmd)
    if match:
        prog = match.group(1)
        fixed = cmd[:match.start()] + f"Get-Command {prog}" + cmd[match.end():]
        return fixed, f"PS-12: 'which {prog}' → 'Get-Command {prog}'"
    return cmd, None


# ---------------------------------------------------------------------------
# PS-13: Single quotes with $variables — Detect only
# ---------------------------------------------------------------------------
_SINGLE_QUOTE_VAR_RE = re.compile(r"'[^']*\$\w+[^']*'")


def _detect_13_single_quote_var(cmd: str) -> str | None:
    if _SINGLE_QUOTE_VAR_RE.search(cmd):
        return "PS-13: variable inside single quotes won't expand. Use double quotes for interpolation."
    return None


# ---------------------------------------------------------------------------
# PS-14: \n literal in strings → `n
# ---------------------------------------------------------------------------
_DQUOTE_STRING_RE = re.compile(r'"([^"]*)"')


def _replace_escapes_in_dquote(m: re.Match[str]) -> str:
    """Replace \\n \\t \\r inside a double-quoted string with `n `t `r."""
    inner = m.group(1)
    inner = inner.replace("\\n", "`n").replace("\\t", "`t").replace("\\r", "`r")
    return f'"{inner}"'


def _fix_14_escape_n(cmd: str) -> tuple[str, str | None]:
    if re.search(r'"[^"]*\\[ntr][^"]*"', cmd):
        fixed = _DQUOTE_STRING_RE.sub(_replace_escapes_in_dquote, cmd)
        return fixed, r"PS-14: replaced '\n','\t','\r' with '`n','`t','`r' inside double-quoted strings"
    return cmd, None


# ---------------------------------------------------------------------------
# PS-15: stderr redirect patterns — Detect only
# ---------------------------------------------------------------------------

def _detect_15_stderr(cmd: str) -> str | None:
    if "2>&1" in cmd and "|" in cmd:
        # Check if 2>&1 is AFTER the pipe (wrong order)
        pipe_pos = cmd.index("|")
        redir_pos = cmd.index("2>&1")
        if redir_pos > pipe_pos:
            return "PS-15: '2>&1' should come BEFORE '|', not after. Move it: cmd 2>&1 | ..."
    return None


# ---------------------------------------------------------------------------
# PS-16: Backslash escape — Detect-only (too context-dependent)
# ---------------------------------------------------------------------------

def _detect_16_backslash_escape(cmd: str) -> str | None:
    # Only warn if backslash looks like an escape (not a path separator)
    if re.search(r'\\[ntrb0]', cmd) and '"' in cmd:
        return r"PS-16: PS escape char is backtick (`) not backslash (\). Use `n `t `r instead of \n \t \r"
    return None


# ---------------------------------------------------------------------------
# PS-17: powershell -c subshell — Detect only
# ---------------------------------------------------------------------------
_SUBSHELL_RE = re.compile(r"\bpowershell(?:\.exe)?\s+-[cC]\s+")


def _detect_17_subshell(cmd: str) -> str | None:
    if _SUBSHELL_RE.search(cmd):
        return "PS-17: 'powershell -c' creates subshell — loses venv, cwd, env vars. Run directly instead."
    return None


# ---------------------------------------------------------------------------
# Master pipeline
# ---------------------------------------------------------------------------

# Auto-fix functions (safe to apply automatically)
_AUTO_FIXES = [
    _fix_01_and_chain,       # PS-01: && → ;
    _fix_02_angle_brackets,  # PS-02: <file> → [file]
    _fix_03_unquoted_paths,  # PS-03: quote paths with spaces
    _fix_05_export,          # PS-05: export → $env:
    _fix_07_grep,            # PS-07: grep → Select-String
    _fix_08_head_tail,       # PS-08: head/tail/wc → PS equivalents
    _fix_09_rm_rf,           # PS-09: rm -rf → Remove-Item
    _fix_10_ls_flags,        # PS-10: ls -la → Get-ChildItem
    _fix_11_touch,           # PS-11: touch → New-Item
    _fix_12_which,           # PS-12: which → Get-Command
    _fix_14_escape_n,        # PS-14: \n → `n
]

# Detect-only functions (context-dependent, return warnings)
_DETECTORS = [
    _detect_04_heredoc,           # PS-04: heredoc
    _detect_06_subexpression,     # PS-06: $() in quotes
    _detect_13_single_quote_var,  # PS-13: '$var'
    _detect_15_stderr,            # PS-15: 2>&1 order
    _detect_16_backslash_escape,  # PS-16: \ escape
    _detect_17_subshell,          # PS-17: powershell -c
]


def fix_powershell_command(command: str) -> FixResult:
    """Apply all auto-fixes and detect warnings for a PowerShell command.

    Returns FixResult with:
    - fixed command string
    - list of applied fixes (with PS-XX IDs)
    - list of warnings for context-dependent issues
    """
    current = command
    fixes_applied: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    # Phase 1: Auto-fix (12 safe patterns)
    for fix_fn in _AUTO_FIXES:
        result, description = fix_fn(current)
        if description:
            fix_id = description.split(":")[0]  # e.g. "PS-01"
            fixes_applied.append({"id": fix_id, "description": description})
            current = result

    # Phase 2: Detect warnings (5 context-dependent patterns)
    for detect_fn in _DETECTORS:
        warning = detect_fn(current)
        if warning:
            warn_id = warning.split(":")[0]
            warnings.append({"id": warn_id, "description": warning})

    return FixResult(
        original=command,
        fixed=current,
        was_modified=current != command,
        fixes_applied=fixes_applied,
        warnings=warnings,
    )
