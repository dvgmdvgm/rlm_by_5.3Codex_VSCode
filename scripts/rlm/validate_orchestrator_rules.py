"""Deterministic post-orchestration rules validator.

Parses orchestrator_state.json and canonical coding_rules.md to find
operational rules that were never executed during the orchestration run.
Outputs a compact JSON report that a lightweight LLM agent can act on.

Usage:
    python scripts/rlm/validate_orchestrator_rules.py \
        --project-root "<path>" \
        [--memory-dir memory] \
        [--state-file .vscode/tasks/orchestrator_state.json]

Exit codes:
    0 — all operational rules were addressed (or no operational rules exist)
    1 — missed rules detected (see output JSON)
    2 — input error (missing files, parse failure)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
        except OSError:
            return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def extract_operational_rules(coding_rules_text: str) -> list[dict]:
    """Extract entities that look like operational rules from coding_rules.md.

    Operational rules have structured JSON payloads containing rule_id, scope,
    trigger, action fields. We also detect rules with 'rule' type marker.
    """
    rules: list[dict] = []
    current_entity: str | None = None

    for line in coding_rules_text.splitlines():
        # Detect entity headers: ### <entity_name>
        header_match = re.match(r"^###\s+(\S+)", line)
        if header_match:
            current_entity = header_match.group(1)
            continue

        if not current_entity:
            continue

        # Look for [rule][active] markers
        if re.search(r"\[rule\]\[active", line, re.IGNORECASE):
            # Extract the description text after the markers
            desc_match = re.search(r"\]\s*(.+?)(?:\s*\(source:.*\))?$", line)
            description = desc_match.group(1).strip() if desc_match else line.strip()

            # Try to parse embedded JSON from the description
            rule_info: dict = {
                "entity": current_entity,
                "description": description,
                "has_structured_payload": False,
            }

            # Check if description contains JSON with rule_id/scope/trigger/action
            json_match = re.search(r"\{.*\"rule_id\".*\}", description, re.DOTALL)
            if json_match:
                try:
                    payload = json.loads(json_match.group(0))
                    rule_info["rule_id"] = payload.get("rule_id", current_entity)
                    rule_info["scope"] = payload.get("scope", "unknown")
                    rule_info["trigger"] = payload.get("trigger", "unknown")
                    rule_info["action"] = payload.get("action", "unknown")
                    rule_info["preconditions"] = payload.get("preconditions", "")
                    rule_info["failure_policy"] = payload.get("failure_policy", "non-blocking")
                    rule_info["has_structured_payload"] = True
                except json.JSONDecodeError:
                    rule_info["rule_id"] = current_entity
            else:
                rule_info["rule_id"] = current_entity

            rules.append(rule_info)

    return rules


def extract_executed_rules_from_state(state: dict) -> set[str]:
    """Extract rule IDs that appear in last_gate_tokens or rules_audit_accumulated."""
    executed: set[str] = set()

    # Check rules_audit_accumulated
    audit_entries = state.get("rules_audit_accumulated", [])
    if isinstance(audit_entries, list):
        for entry in audit_entries:
            if isinstance(entry, dict):
                rule_id = entry.get("rule_id") or entry.get("entity", "")
                status = entry.get("status", "")
                if status in ("applied", "executed", "matched"):
                    executed.add(rule_id)

    # Check last_gate_tokens for any RULES_EXECUTED > 0
    gate_tokens = state.get("last_gate_tokens", {})
    if isinstance(gate_tokens, dict):
        for task_id, token_str in gate_tokens.items():
            if isinstance(token_str, str) and "RULES_EXECUTED" in token_str:
                match = re.search(r"RULES_EXECUTED:\s*(\d+)", token_str)
                if match and int(match.group(1)) > 0:
                    # Rules were executed but we don't know which ones from this field alone
                    pass

    return executed


def extract_executed_rules_from_audit_log(audit_path: Path) -> set[str]:
    """Extract executed rule IDs from orchestration_audit.jsonl if available."""
    executed: set[str] = set()
    text = read_text(audit_path)
    if not text.strip():
        return executed

    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            if entry.get("event") in ("rule_executed", "rule_matched", "synthesizer_operational_rules_gate_ok"):
                rule_id = entry.get("rule_id", "")
                if rule_id:
                    executed.add(rule_id)
            # Also check notes field for rule references
            notes = entry.get("notes", "")
            if "RULES_EXECUTED" in str(notes):
                pass  # Already covered
        except json.JSONDecodeError:
            continue

    return executed


def extract_executed_rules_from_checklist(checklist_path: Path) -> set[str]:
    """Fallback: extract any rule references from orchestrator_memory_checklist.md."""
    executed: set[str] = set()
    text = read_text(checklist_path)
    # Look for rule_id mentions in checklist
    for match in re.finditer(r"rule_id[:\s]+(\S+)", text, re.IGNORECASE):
        executed.add(match.group(1))
    return executed


def build_validation_report(
    *,
    project_root: Path,
    memory_dir: Path,
    state_path: Path,
) -> dict:
    """Build the validation report comparing operational rules vs executed rules."""

    # 1. Load orchestrator state
    state_text = read_text(state_path)
    if not state_text.strip():
        return {
            "status": "error",
            "error": f"orchestrator_state.json not found or empty at {state_path}",
            "missed_rules": [],
            "total_operational_rules": 0,
            "total_executed": 0,
        }

    try:
        state = json.loads(state_text)
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"Failed to parse orchestrator_state.json: {e}",
            "missed_rules": [],
            "total_operational_rules": 0,
            "total_executed": 0,
        }

    # 2. Load canonical coding rules and extract operational rules
    coding_rules_path = memory_dir / "canonical" / "coding_rules.md"
    coding_rules_text = read_text(coding_rules_path)
    operational_rules = extract_operational_rules(coding_rules_text)

    if not operational_rules:
        return {
            "status": "pass",
            "message": "No operational rules with [rule][active] found in canonical memory",
            "missed_rules": [],
            "total_operational_rules": 0,
            "total_executed": 0,
        }

    # 3. Gather executed rule IDs from all available sources
    executed_ids: set[str] = set()
    executed_ids |= extract_executed_rules_from_state(state)

    # Check audit log
    audit_log_path = project_root / ".vscode" / "tasks" / "orchestration_audit.jsonl"
    executed_ids |= extract_executed_rules_from_audit_log(audit_log_path)

    # Check memory logs for audit backups
    for p in (memory_dir / "logs").glob("orchestration_audit_*.jsonl"):
        executed_ids |= extract_executed_rules_from_audit_log(p)

    # Check checklist
    checklist_path = memory_dir / "logs" / "orchestrator_memory_checklist.md"
    executed_ids |= extract_executed_rules_from_checklist(checklist_path)

    # 4. Determine missed rules
    missed: list[dict] = []
    for rule in operational_rules:
        rule_id = rule["rule_id"]
        entity = rule["entity"]
        if rule_id not in executed_ids and entity not in executed_ids:
            missed.append({
                "rule_id": rule_id,
                "entity": entity,
                "description": rule.get("description", ""),
                "scope": rule.get("scope", "unknown"),
                "trigger": rule.get("trigger", "unknown"),
                "action": rule.get("action", "unknown"),
                "has_structured_payload": rule.get("has_structured_payload", False),
            })

    # 5. Build report
    status = "fail" if missed else "pass"
    return {
        "status": status,
        "total_operational_rules": len(operational_rules),
        "total_executed": len(operational_rules) - len(missed),
        "total_missed": len(missed),
        "missed_rules": missed,
        "executed_rule_ids": sorted(executed_ids) if executed_ids else [],
        "orchestrator_phase": state.get("phase", "unknown"),
        "tasks_completed": state.get("tasks_completed", []),
        "tasks_remaining": state.get("tasks_remaining", []),
    }


def write_report(report: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic post-orchestration rules validator."
    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--memory-dir", default="memory", help="Memory dir relative to project root")
    parser.add_argument(
        "--state-file",
        default=".vscode/tasks/orchestrator_state.json",
        help="Orchestrator state file relative to project root",
    )
    parser.add_argument(
        "--output",
        default=".vscode/tasks/validation_report.json",
        help="Output report path relative to project root",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    memory_dir = (project_root / args.memory_dir).resolve()
    state_path = (project_root / args.state_file).resolve()
    output_path = (project_root / args.output).resolve()

    report = build_validation_report(
        project_root=project_root,
        memory_dir=memory_dir,
        state_path=state_path,
    )

    write_report(report, output_path)

    # Print compact summary to stdout
    print(f"[validator] status={report['status']}")
    print(f"[validator] operational_rules={report['total_operational_rules']}")
    print(f"[validator] executed={report.get('total_executed', 0)}")
    print(f"[validator] missed={report.get('total_missed', 0)}")
    print(f"[validator] output={output_path.as_posix()}")

    if report["missed_rules"]:
        print("[validator] missed rule IDs:")
        for r in report["missed_rules"]:
            print(f"  - {r['rule_id']}: {r.get('action', 'unknown action')}")

    if report["status"] == "fail":
        return 1
    if report["status"] == "error":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
