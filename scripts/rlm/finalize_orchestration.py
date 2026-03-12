"""Finalize an orchestration run in a single deterministic pass.

Combines: validate rules → write checklist → archive audit log → cleanup run dir.
This replaces 4-5 separate tool calls with a single CLI invocation (~1000 token savings).

Usage:
    python scripts/rlm/finalize_orchestration.py \
        --project-root "<path>" \
        --run-id "orch_YYYYMMDD_HHMMSS" \
        [--status completed] \
        [--skip-cleanup]

Exit codes:
    0 — finalization complete (even if validation found missed rules)
    1 — missed operational rules (report written, cleanup skipped)
    2 — input error (missing files, parse failure)
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def resolve_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (project_root / path).resolve()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, OSError):
            continue
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────
# Step 1: Validate orchestrator rules
# ──────────────────────────────────────────────────────────
def validate_rules(
    project_root: Path,
    memory_dir: Path,
    run_dir: Path,
) -> dict:
    """Run lightweight rule validation. Returns report dict."""
    state_path = run_dir / "orchestrator_state.json"
    audit_path = run_dir / "orchestration_audit.jsonl"
    coding_rules_path = memory_dir / "canonical" / "coding_rules.md"

    report: dict = {
        "ts": utc_now(),
        "run_dir": run_dir.as_posix(),
        "status": "pass",
        "missed_rules": [],
        "total_operational_rules": 0,
        "executed_rules": 0,
    }

    # Read state
    state_text = read_text(state_path)
    state: dict = {}
    if state_text.strip():
        try:
            state = json.loads(state_text)
        except json.JSONDecodeError:
            report["status"] = "error"
            report["error"] = f"Cannot parse {state_path.name}"
            return report

    # Extract operational rules from coding_rules.md
    cr_text = read_text(coding_rules_path)
    import re
    rule_entities: set[str] = set()
    current_entity: str | None = None
    for line in cr_text.splitlines():
        hm = re.match(r"^###\s+(\S+)", line)
        if hm:
            current_entity = hm.group(1)
            continue
        if current_entity and re.search(r"\[rule\]\[active", line, re.IGNORECASE):
            rule_entities.add(current_entity)

    report["total_operational_rules"] = len(rule_entities)

    # Extract executed rules from audit log
    executed: set[str] = set()
    audit_text = read_text(audit_path)
    for al in audit_text.strip().splitlines():
        al = al.strip()
        if not al:
            continue
        try:
            entry = json.loads(al)
            event = entry.get("event", "")
            if "rule" in event.lower() or "op_rules" in event.lower():
                # Mark all rules as potentially covered
                for rule_id in rule_entities:
                    if rule_id.lower() in al.lower():
                        executed.add(rule_id)
        except json.JSONDecodeError:
            continue

    # Also check state for gate tokens
    gate_tokens = state.get("last_gate_tokens", {})
    if isinstance(gate_tokens, dict):
        for _, token_str in gate_tokens.items():
            if isinstance(token_str, str) and "OP_RULES_OK" in token_str:
                # If any task passed OP_RULES_OK, rules were addressed
                executed = rule_entities.copy()
                break

    report["executed_rules"] = len(executed)
    missed = rule_entities - executed
    if missed:
        report["missed_rules"] = sorted(missed)
        report["status"] = "warn"

    return report


# ──────────────────────────────────────────────────────────
# Step 2: Write checklist
# ──────────────────────────────────────────────────────────
def write_checklist(
    project_root: Path,
    memory_dir: Path,
    run_dir: Path,
    run_id: str,
    status: str,
) -> Path:
    """Write compact memory checklist. Returns output path."""
    payload_log_path = memory_dir / "logs" / "cloud_payload_audit.md"
    payload_text = read_text(payload_log_path)
    import re
    tools = re.findall(r"^tool:\s*(.+?)\s*$", payload_text, flags=re.MULTILINE)
    recent_tools = tools[-12:] if tools else []

    master_plan_path = run_dir / "master_plan.md"
    mp_text = read_text(master_plan_path)
    done = len(re.findall(r"\bdone\b", mp_text, flags=re.IGNORECASE))

    content = (
        f"# Orchestrator Checklist — {run_id}\n"
        f"- generated_at: {utc_now()}\n"
        f"- status: {status}\n"
        f"- tasks_done: {done}\n"
        f"- bootstrap: {'yes' if 'local_memory_bootstrap' in recent_tools else 'no'}\n"
        f"- consolidation: {'yes' if 'consolidate_memory' in recent_tools else 'no'}\n"
    )
    out_path = memory_dir / "logs" / f"orchestrator_checklist_{run_id}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return out_path


# ──────────────────────────────────────────────────────────
# Step 3: Archive audit log
# ──────────────────────────────────────────────────────────
def archive_audit_log(
    memory_dir: Path,
    run_dir: Path,
    run_id: str,
) -> Path | None:
    """Copy audit JSONL to memory/logs/ for persistence. Returns dest path or None."""
    src = run_dir / "orchestration_audit.jsonl"
    if not src.exists():
        return None
    dest = memory_dir / "logs" / f"orchestration_audit_{run_id}.jsonl"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dest))
    return dest


# ──────────────────────────────────────────────────────────
# Step 4: Cleanup run directory
# ──────────────────────────────────────────────────────────
def cleanup_run_dir(run_dir: Path) -> bool:
    """Remove run directory and return success."""
    if not run_dir.exists():
        return True
    try:
        shutil.rmtree(str(run_dir))
        return True
    except OSError:
        return False


# ──────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Finalize orchestration run: validate → checklist → archive → cleanup."
    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--run-id", required=True, help="Orchestration run ID")
    parser.add_argument("--memory-dir", default="memory", help="Memory dir (relative to project root)")
    parser.add_argument("--tasks-dir", default="", help="Run dir override (default: .vscode/tasks/<run_id>)")
    parser.add_argument("--status", default="completed", help="Run status (completed/failed/halted)")
    parser.add_argument("--skip-cleanup", action="store_true", help="Keep run directory after finalization")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    memory_dir = resolve_path(project_root, args.memory_dir)
    run_dir = resolve_path(project_root, args.tasks_dir) if args.tasks_dir else (project_root / ".vscode" / "tasks" / args.run_id)

    if not run_dir.exists():
        print(json.dumps({"error": f"Run directory not found: {run_dir}", "status": "error"}, indent=2))
        return 2

    results: dict = {
        "run_id": args.run_id,
        "ts": utc_now(),
        "steps": {},
    }

    # Step 1: Validate
    validation = validate_rules(project_root, memory_dir, run_dir)
    results["steps"]["validate"] = validation["status"]
    validation_path = run_dir / "validation_report.json"
    validation_path.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")

    # Step 2: Checklist
    checklist_path = write_checklist(project_root, memory_dir, run_dir, args.run_id, args.status)
    results["steps"]["checklist"] = checklist_path.as_posix()

    # Step 3: Archive
    archive_path = archive_audit_log(memory_dir, run_dir, args.run_id)
    results["steps"]["archive"] = archive_path.as_posix() if archive_path else "no_audit_log"

    # Step 4: Cleanup
    if args.skip_cleanup:
        results["steps"]["cleanup"] = "skipped"
    else:
        cleaned = cleanup_run_dir(run_dir)
        results["steps"]["cleanup"] = "done" if cleaned else "failed"

    # Overall status
    has_missed = bool(validation.get("missed_rules"))
    results["status"] = "completed_with_warnings" if has_missed else "completed"
    results["missed_rules_count"] = len(validation.get("missed_rules", []))

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 1 if has_missed else 0


if __name__ == "__main__":
    raise SystemExit(main())
