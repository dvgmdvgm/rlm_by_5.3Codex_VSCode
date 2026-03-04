from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .time_policy import DEFAULT_TIMESTAMP_MODE, now_dt, now_iso


@dataclass
class ConsolidationResult:
    log_path: str
    total_log_records: int
    extracted_fact_records: int
    unique_facts: int
    architecture_items: int
    coding_rules_items: int
    active_tasks_items: int
    architecture_path: str
    coding_rules_path: str
    active_tasks_path: str
    changelog_path: str | None
    conflicts_resolved: int


@dataclass
class FactItem:
    type: str
    entity: str
    date: str
    value: str
    source: str
    ts: str
    priority: int
    status: str
    conflict_key: str


def _normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _to_epoch(ts: str) -> float:
    if not ts:
        return 0.0
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _source_rank(source: str) -> int:
    src = source.lower()
    if src.startswith("session:"):
        return 3
    if src.startswith("memory/changelog/"):
        return 2
    if src.startswith("memory/"):
        return 1
    return 0


def _infer_conflict_key(entity: str, value: str, fact_type: str) -> str:
    if fact_type.lower() != "rule":
        return ""
    text = f"{entity} {value}".lower()
    if "button" in text and "color" in text:
        return "ui_buttons_color"
    if "all website buttons" in text:
        return "ui_buttons_color"
    return ""


def _pick_winner(items: list[FactItem]) -> FactItem:
    def _score(item: FactItem) -> tuple[int, int, float, int]:
        active_rank = 1 if item.status.lower() == "active" else 0
        return (
            active_rank,
            item.priority,
            _to_epoch(item.ts),
            _source_rank(item.source),
        )

    return max(items, key=_score)


def _classify_fact(fact: FactItem) -> str:
    """Classify a fact into a canonical bucket.

    Two-level routing:
    1. Primary signal — ``fact.type`` (the inner type field set by the author).
       Explicit type values map directly to buckets without keyword scanning,
       so ``type=rule`` always lands in coding_rules even if the text
       contains task-like words such as "fix" or "plan".
    2. Fallback — keyword scanning over entity + value (NOT type) with
       word-boundary matching to avoid false substring hits.
    """
    fact_type = fact.type.lower().strip()

    # --- Level 1: explicit type → deterministic bucket ---
    _type_to_bucket: dict[str, str] = {
        "rule": "coding_rules",
        "policy": "coding_rules",
        "convention": "coding_rules",
        "style": "coding_rules",
        "lint": "coding_rules",
        "architecture": "architecture",
        "section": "architecture",
        "api": "architecture",
        "task": "active_tasks",
        "todo": "active_tasks",
    }
    if fact_type in _type_to_bucket:
        return _type_to_bucket[fact_type]

    # --- Level 2: keyword scan on entity + value only (no fact_type) ---
    source = fact.source.lower()
    entity = fact.entity.lower()
    value = fact.value.lower()
    blob = " | ".join([source, entity, value])

    # Compile word-boundary patterns to avoid substring false positives
    # (e.g. "plan" matching "explanation", "fix" matching "prefix").
    def _wb_match(markers: list[str], text: str) -> bool:
        for m in markers:
            if re.search(r"\b" + re.escape(m) + r"\b", text):
                return True
        return False

    task_markers = [
        "task", "todo", "next step", "plan", "fix", "bug",
        "implement", "pending", "roadmap", "migration",
    ]
    rule_markers = [
        "rule", "policy", "token", "design system", "coding",
        "naming", "style", "convention", "lint", "theme",
    ]
    arch_markers = [
        "architecture", "screens_architecture", "project_architecture",
        "system", "layer", "module",
    ]

    # Priority: rules > tasks > architecture (rules are the most common
    # target for explicit user-saved facts; tasks only win if the text
    # is unambiguously task-oriented).
    if _wb_match(rule_markers, blob):
        return "coding_rules"
    if _wb_match(task_markers, blob):
        return "active_tasks"
    if _wb_match(arch_markers, blob):
        return "architecture"

    # Fallback: coding_rules is the safest default for unclassified facts.
    return "coding_rules"


def _render_markdown(title: str, doc_id: str, source_log: str, items: list[FactItem]) -> str:
    now = now_iso(DEFAULT_TIMESTAMP_MODE)
    rows: list[str] = [
        f"# {title}",
        "",
        "## META",
        f"- id: {doc_id}",
        f"- updated_at: {now}",
        f"- source: {source_log}",
        f"- items: {len(items)}",
        "",
    ]

    grouped: dict[str, list[FactItem]] = {}
    for item in items:
        group_name = item.entity or "General"
        grouped.setdefault(group_name, []).append(item)

    for group_name, group_items in sorted(grouped.items(), key=lambda x: x[0].lower()):
        rows.append(f"### {group_name}")
        for item in group_items:
            source = item.source
            status = item.status.lower()
            priority = item.priority
            marker = f"[{item.type}][{status};p={priority}]"
            if source:
                rows.append(
                    f"- {marker} {item.value} (source: {source})"
                )
            else:
                rows.append(f"- {marker} {item.value}")
        rows.append("")

    return "\n".join(rows).strip() + "\n"


def consolidate_memory(
    *,
    memory_dir: Path,
    log_rel_path: str = "logs/extracted_facts.jsonl",
    write_changelog: bool = True,
) -> ConsolidationResult:
    memory_dir.mkdir(parents=True, exist_ok=True)

    log_path = memory_dir / log_rel_path
    canonical_dir = memory_dir / "canonical"
    changelog_dir = memory_dir / "changelog"
    canonical_dir.mkdir(parents=True, exist_ok=True)
    changelog_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                records.append(parsed)

    facts: list[FactItem] = []
    source_records: list[dict[str, Any]] = []
    for record in records:
        if record.get("type") != "extracted_fact":
            continue
        value = record.get("value")
        if isinstance(value, dict):
            source_records.append(record)
            facts.append(
                FactItem(
                    type=_normalize_text(value.get("type", "")),
                    entity=_normalize_text(value.get("entity", "")),
                    date=_normalize_text(value.get("date", "")),
                    value=_normalize_text(value.get("value", "")),
                    source=_normalize_text(value.get("source", "")),
                    ts=_normalize_text(record.get("ts", "")),
                    priority=int(value.get("priority", 0)) if str(value.get("priority", "0")).lstrip("-").isdigit() else 0,
                    status=_normalize_text(value.get("status", "active")) or "active",
                    conflict_key=_normalize_text(value.get("conflict_key", "")),
                )
            )

    buckets: dict[str, list[FactItem]] = {
        "architecture": [],
        "coding_rules": [],
        "active_tasks": [],
    }

    # keep latest metadata for exact same normalized rule text
    latest_by_text: dict[str, FactItem] = {}
    for fact in facts:
        dedupe_key = json.dumps(
            {
                "type": fact.type,
                "entity": fact.entity,
                "date": fact.date,
                "value": fact.value,
                "source": fact.source,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        existing = latest_by_text.get(dedupe_key)
        if not existing or _to_epoch(fact.ts) >= _to_epoch(existing.ts):
            latest_by_text[dedupe_key] = fact

    deduped_facts = list(latest_by_text.values())

    # detect and resolve conflicts among coding rules using conflict_key
    conflicts: dict[str, list[FactItem]] = {}
    for item in deduped_facts:
        if not item.conflict_key:
            item.conflict_key = _infer_conflict_key(item.entity, item.value, item.type)
        if item.conflict_key:
            conflicts.setdefault(item.conflict_key, []).append(item)

    conflicts_resolved = 0
    for key, items in conflicts.items():
        if len(items) < 2:
            continue
        winner = _pick_winner(items)
        for item in items:
            if item is winner:
                item.status = "active"
            else:
                item.status = "deprecated"
        conflicts_resolved += 1

    # publish only active facts into canonical buckets
    seen_active: set[str] = set()
    for fact in deduped_facts:
        if fact.status.lower() != "active":
            continue
        active_key = json.dumps(
            {
                "type": fact.type,
                "entity": fact.entity,
                "date": fact.date,
                "value": fact.value,
                "source": fact.source,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        if active_key in seen_active:
            continue
        seen_active.add(active_key)
        bucket = _classify_fact(fact)
        buckets[bucket].append(fact)

    architecture_path = canonical_dir / "architecture.md"
    coding_rules_path = canonical_dir / "coding_rules.md"
    active_tasks_path = canonical_dir / "active_tasks.md"

    architecture_md = _render_markdown(
        title="Canonical Architecture Memory",
        doc_id="architecture",
        source_log=f"memory/{log_rel_path}",
        items=buckets["architecture"],
    )
    coding_rules_md = _render_markdown(
        title="Canonical Coding Rules Memory",
        doc_id="coding_rules",
        source_log=f"memory/{log_rel_path}",
        items=buckets["coding_rules"],
    )
    active_tasks_md = _render_markdown(
        title="Canonical Active Tasks Memory",
        doc_id="active_tasks",
        source_log=f"memory/{log_rel_path}",
        items=buckets["active_tasks"],
    )

    architecture_path.write_text(architecture_md, encoding="utf-8")
    coding_rules_path.write_text(coding_rules_md, encoding="utf-8")
    active_tasks_path.write_text(active_tasks_md, encoding="utf-8")

    changelog_path: Path | None = None
    if write_changelog:
        stamp = now_dt(DEFAULT_TIMESTAMP_MODE).strftime("%Y%m%d_%H%M%S")
        changelog_path = changelog_dir / f"rlm_consolidation_{stamp}.md"
        changelog_md = "\n".join(
            [
                "# RLM Consolidation Pass",
                "",
                "## META",
                f"- id: rlm_consolidation_{stamp}",
                f"- updated_at: {now_iso(DEFAULT_TIMESTAMP_MODE)}",
                f"- source: memory/{log_rel_path}",
                "",
                "### Summary",
                f"- total_log_records: {len(records)}",
                f"- extracted_fact_records: {len(facts)}",
                f"- unique_facts: {len(deduped_facts)}",
                f"- active_facts: {len(seen_active)}",
                f"- conflicts_resolved: {conflicts_resolved}",
                f"- architecture_items: {len(buckets['architecture'])}",
                f"- coding_rules_items: {len(buckets['coding_rules'])}",
                f"- active_tasks_items: {len(buckets['active_tasks'])}",
                "",
                "### Outputs",
                f"- {(architecture_path).as_posix()}",
                f"- {(coding_rules_path).as_posix()}",
                f"- {(active_tasks_path).as_posix()}",
            ]
        ) + "\n"
        changelog_path.write_text(changelog_md, encoding="utf-8")

    return ConsolidationResult(
        log_path=log_path.as_posix(),
        total_log_records=len(records),
        extracted_fact_records=len(facts),
        unique_facts=len(deduped_facts),
        architecture_items=len(buckets["architecture"]),
        coding_rules_items=len(buckets["coding_rules"]),
        active_tasks_items=len(buckets["active_tasks"]),
        architecture_path=architecture_path.as_posix(),
        coding_rules_path=coding_rules_path.as_posix(),
        active_tasks_path=active_tasks_path.as_posix(),
        changelog_path=changelog_path.as_posix() if changelog_path else None,
        conflicts_resolved=conflicts_resolved,
    )
