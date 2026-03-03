#!/usr/bin/env python3
"""
One-time migration: convert non-standard extracted_facts.jsonl records
into the strict canonical format.

Canonical format (the ONLY format the consolidator accepts):
  {"type": "extracted_fact", "ts": "<ISO-8601>", "value": {
    "type": "<rule|task|fix|decision|change|analysis|feature|review|architecture|api>",
    "entity": "<short_snake_case_id>",
    "date": "<YYYY-MM-DD>",
    "value": "<concise description>",
    "source": "session:<session_id>",
    "priority": <0-10>,
    "status": "active"
  }}

Known legacy formats handled:
  A) {"ts": ..., "session": ..., "facts": [...]}          — no outer type
  B) {"timestamp": ..., "type": "feature", ...}           — wrong outer type
  C) {"timestamp": ..., "type": "extracted_fact", ...}    — flat layout (no nested value dict)
  D) {"type": "git_push", ...}                            — arbitrary outer type

Usage:
  python scripts/migrate_legacy_facts.py <path_to_extracted_facts.jsonl> [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def _normalize_ts(record: dict) -> str:
    """Extract best available timestamp as ISO-8601 UTC string."""
    raw = record.get("ts") or record.get("timestamp") or ""
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(raw, str):
        return raw
    return str(raw)


def _extract_date(ts: str) -> str:
    """Extract YYYY-MM-DD from an ISO timestamp string."""
    match = re.match(r"(\d{4}-\d{2}-\d{2})", ts)
    return match.group(1) if match else datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _snake_case(text: str) -> str:
    """Best-effort conversion to short snake_case entity id."""
    text = re.sub(r"[^a-zA-Z0-9_\s]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text.lower()[:60] or "unknown"


def _is_canonical(record: dict) -> bool:
    """Check if record already matches the strict canonical schema."""
    if record.get("type") != "extracted_fact":
        return False
    value = record.get("value")
    if not isinstance(value, dict):
        return False
    required = {"type", "entity", "value", "source", "priority", "status"}
    return required.issubset(value.keys())


def _migrate_session_facts(record: dict) -> list[dict]:
    """Format A: {"ts":..., "session":..., "facts":[...]}"""
    ts = _normalize_ts(record)
    date = _extract_date(ts)
    session = record.get("session", "unknown_session")
    facts_list = record.get("facts", [])
    results = []

    for fact in facts_list:
        if isinstance(fact, dict):
            file_changed = fact.get("file", "")
            change_desc = fact.get("change", "") or fact.get("description", "") or json.dumps(fact, ensure_ascii=False)
            entity = _snake_case(session)
            results.append({
                "type": "extracted_fact",
                "ts": ts,
                "value": {
                    "type": "change",
                    "entity": entity,
                    "date": date,
                    "value": f"{file_changed}: {change_desc}".strip(": ") if file_changed else change_desc,
                    "source": f"session:{session}",
                    "priority": 7,
                    "status": "active",
                },
            })
        elif isinstance(fact, str):
            results.append({
                "type": "extracted_fact",
                "ts": ts,
                "value": {
                    "type": "change",
                    "entity": _snake_case(session),
                    "date": date,
                    "value": fact,
                    "source": f"session:{session}",
                    "priority": 7,
                    "status": "active",
                },
            })
    return results


def _migrate_flat_record(record: dict) -> list[dict]:
    """Formats B/C/D: flat records with wrong or missing outer type."""
    ts = _normalize_ts(record)
    date = _extract_date(ts)

    original_type = record.get("type", "change")
    if original_type == "extracted_fact":
        original_type = "change"  # flat extracted_fact — type was outer, need inner

    session = record.get("session", "unknown_session")
    summary = record.get("summary", "") or record.get("description", "") or record.get("value", "")
    if not isinstance(summary, str):
        try:
            summary = json.dumps(summary, ensure_ascii=False)
        except Exception:
            summary = str(summary)

    # Handle records with embedded facts list
    if "facts" in record and isinstance(record["facts"], list):
        return _migrate_session_facts(record)

    # Try to extract scope info
    scope = record.get("scope", [])
    if isinstance(scope, list) and scope:
        scope_str = ", ".join(scope[:3])
        if summary:
            summary = f"[{scope_str}] {summary}"

    # Detect entity
    entity = _snake_case(
        record.get("rule_id", "")
        or record.get("entity", "")
        or session
    )

    # Map type
    valid_types = {"rule", "task", "fix", "decision", "change", "analysis", "feature", "review", "architecture", "api"}
    fact_type = original_type.lower() if original_type.lower() in valid_types else "change"

    # Priority
    priority = record.get("priority", 7)
    if not isinstance(priority, int) or priority < 0 or priority > 10:
        priority = 7

    if not summary:
        # Last resort: serialize the whole record minus known meta fields
        meta_keys = {"type", "ts", "timestamp", "session", "date", "priority", "status"}
        payload = {k: v for k, v in record.items() if k not in meta_keys}
        summary = json.dumps(payload, ensure_ascii=False)[:300]

    return [{
        "type": "extracted_fact",
        "ts": ts,
        "value": {
            "type": fact_type,
            "entity": entity,
            "date": date,
            "value": summary[:500],
            "source": f"session:{session}",
            "priority": priority,
            "status": record.get("status", "active") or "active",
        },
    }]


def migrate_file(path: Path, *, dry_run: bool = False) -> dict:
    """Read JSONL, migrate non-canonical records, write back."""
    lines = path.read_text(encoding="utf-8").splitlines()

    canonical_records: list[dict] = []
    migrated_count = 0
    skipped_count = 0
    already_ok = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            skipped_count += 1
            continue

        if not isinstance(record, dict):
            skipped_count += 1
            continue

        if _is_canonical(record):
            canonical_records.append(record)
            already_ok += 1
            continue

        # Determine which legacy format
        if "facts" in record and isinstance(record.get("facts"), list):
            converted = _migrate_session_facts(record)
        else:
            converted = _migrate_flat_record(record)

        canonical_records.extend(converted)
        migrated_count += len(converted)

    stats = {
        "total_input_lines": len([l for l in lines if l.strip()]),
        "already_canonical": already_ok,
        "migrated": migrated_count,
        "skipped": skipped_count,
        "total_output": len(canonical_records),
    }

    if dry_run:
        print(f"[DRY RUN] {path}")
        print(json.dumps(stats, indent=2))
        if migrated_count > 0:
            print("Sample migrated records:")
            for rec in canonical_records[already_ok:already_ok + 3]:
                print(f"  {json.dumps(rec, ensure_ascii=False)}")
    else:
        # Write back
        output = "\n".join(json.dumps(r, ensure_ascii=False) for r in canonical_records) + "\n"
        path.write_text(output, encoding="utf-8")
        print(f"[MIGRATED] {path}")
        print(json.dumps(stats, indent=2))

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy extracted_facts.jsonl to strict canonical format")
    parser.add_argument("path", help="Path to extracted_facts.jsonl")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(1)

    migrate_file(target, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
