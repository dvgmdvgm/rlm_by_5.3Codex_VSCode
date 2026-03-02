from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class SeedFact:
    fact_type: str
    entity: str
    value: str
    source: str
    priority: int


@dataclass
class CanonicalSummary:
    architecture_items: int
    coding_rules_items: int
    active_tasks_items: int
    changelog_path: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path) -> str:
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


def _collect_items(text: str, max_items: int) -> list[str]:
    items: list[str] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        if line.startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.")):
            cleaned = re.sub(r"^[-*]\s+", "", line)
            cleaned = re.sub(r"^\d+\.\s+", "", cleaned)
            if len(cleaned) >= 12:
                items.append(cleaned)
        if len(items) >= max_items:
            return items

    if items:
        return items[:max_items]

    paragraph = " ".join(lines)
    if not paragraph:
        return []

    parts = re.split(r"(?<=[.!?])\s+", paragraph)
    for part in parts:
        part = part.strip()
        if len(part) >= 16:
            items.append(part)
        if len(items) >= max_items:
            break

    return items[:max_items]


def _map_fact_type(category: str) -> str:
    mapping = {
        "02_architecture": "architecture",
        "03_decisions": "rule",
        "04_domain": "architecture",
        "05_code": "architecture",
        "06_problems": "task",
        "07_context": "architecture",
        "09_external": "architecture",
        "10_testing": "rule",
        "11_deployment": "architecture",
        "12_roadmap": "task",
        "13_preferences": "rule",
        "01_project": "architecture",
    }
    return mapping.get(category, "rule")


def _iter_rlm_files(rlm_root: Path) -> list[Path]:
    if not rlm_root.exists():
        return []
    return sorted(
        path
        for path in rlm_root.glob("**/*.md")
        if path.is_file() and path.name.lower() != "_index.md"
    )


def _to_seed_facts(rlm_root: Path, max_items_per_file: int) -> list[SeedFact]:
    facts: list[SeedFact] = []
    for md_file in _iter_rlm_files(rlm_root):
        rel = md_file.relative_to(rlm_root).as_posix()
        category = rel.split("/")[0]
        fact_type = _map_fact_type(category)
        text = _read_text(md_file)
        if not text.strip():
            continue

        items = _collect_items(text, max_items=max_items_per_file)
        if not items:
            continue

        entity = rel.replace(".md", "")
        priority = 9 if category in {"13_preferences", "03_decisions"} else 7

        for item in items:
            facts.append(
                SeedFact(
                    fact_type=fact_type,
                    entity=entity,
                    value=item,
                    source=f"memory/rlm_memory/{rel}",
                    priority=priority,
                )
            )

    return facts


def _append_extracted_facts(log_path: Path, facts: list[SeedFact], session_tag: str) -> int:
    if not facts:
        return 0

    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = _utc_now()
    date_value = ts[:10]
    written = 0

    with log_path.open("a", encoding="utf-8") as handle:
        for fact in facts:
            payload = {
                "type": "extracted_fact",
                "ts": ts,
                "value": {
                    "type": fact.fact_type,
                    "entity": fact.entity,
                    "date": date_value,
                    "value": fact.value,
                    "source": f"{fact.source}#{session_tag}",
                    "priority": fact.priority,
                    "status": "active",
                },
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            written += 1

    return written


def _read_extracted_facts(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []

    records: list[dict] = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        if row.get("type") != "extracted_fact":
            continue
        value = row.get("value")
        if not isinstance(value, dict):
            continue
        records.append(
            {
                "type": str(value.get("type", "")).strip().lower(),
                "entity": str(value.get("entity", "")).strip(),
                "value": str(value.get("value", "")).strip(),
                "source": str(value.get("source", "")).strip(),
                "status": str(value.get("status", "active")).strip().lower() or "active",
                "priority": int(value.get("priority", 0)) if str(value.get("priority", "0")).lstrip("-").isdigit() else 0,
            }
        )
    return records


def _bucket_for_fact(fact: dict) -> str:
    fact_type = fact.get("type", "")
    if fact_type in {"task", "todo", "review", "change"}:
        return "active_tasks"
    if fact_type in {"rule", "policy", "guideline", "preference"}:
        return "coding_rules"
    return "architecture"


def _render_canonical(title: str, doc_id: str, source_log: str, items: list[dict]) -> str:
    now = _utc_now()
    rows = [
        f"# {title}",
        "",
        "## META",
        f"- id: {doc_id}",
        f"- updated_at: {now}",
        f"- source: {source_log}",
        f"- items: {len(items)}",
        "",
    ]
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(item.get("entity") or "General", []).append(item)

    for entity, entity_items in sorted(grouped.items(), key=lambda x: x[0].lower()):
        rows.append(f"### {entity}")
        for item in entity_items:
            value = item.get("value", "")
            source = item.get("source", "")
            status = item.get("status", "active")
            priority = item.get("priority", 0)
            rows.append(f"- [{item.get('type','')}][{status};p={priority}] {value} (source: {source})")
        rows.append("")

    return "\n".join(rows).rstrip() + "\n"


def _write_canonical_from_log(memory_dir: Path, log_rel_path: str = "logs/extracted_facts.jsonl") -> CanonicalSummary:
    log_path = memory_dir / log_rel_path
    canonical_dir = memory_dir / "canonical"
    changelog_dir = memory_dir / "changelog"
    canonical_dir.mkdir(parents=True, exist_ok=True)
    changelog_dir.mkdir(parents=True, exist_ok=True)

    records = _read_extracted_facts(log_path)
    dedupe: dict[tuple[str, str, str, str], dict] = {}
    for row in records:
        if row.get("status") != "active":
            continue
        key = (row.get("type", ""), row.get("entity", ""), row.get("value", ""), row.get("source", ""))
        if key not in dedupe:
            dedupe[key] = row

    buckets = {
        "architecture": [],
        "coding_rules": [],
        "active_tasks": [],
    }
    for row in dedupe.values():
        bucket = _bucket_for_fact(row)
        buckets[bucket].append(row)

    arch_path = canonical_dir / "architecture.md"
    rules_path = canonical_dir / "coding_rules.md"
    tasks_path = canonical_dir / "active_tasks.md"

    arch_path.write_text(
        _render_canonical(
            title="Canonical Architecture Memory",
            doc_id="architecture",
            source_log=f"memory/{log_rel_path}",
            items=buckets["architecture"],
        ),
        encoding="utf-8",
    )
    rules_path.write_text(
        _render_canonical(
            title="Canonical Coding Rules Memory",
            doc_id="coding_rules",
            source_log=f"memory/{log_rel_path}",
            items=buckets["coding_rules"],
        ),
        encoding="utf-8",
    )
    tasks_path.write_text(
        _render_canonical(
            title="Canonical Active Tasks Memory",
            doc_id="active_tasks",
            source_log=f"memory/{log_rel_path}",
            items=buckets["active_tasks"],
        ),
        encoding="utf-8",
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    changelog_path = changelog_dir / f"seed_canonical_{stamp}.md"
    changelog_body = "\n".join(
        [
            "# Canonical Seed Run",
            "",
            "## META",
            f"- generated_at: {_utc_now()}",
            f"- source_log: memory/{log_rel_path}",
            "",
            "## Counts",
            f"- architecture_items: {len(buckets['architecture'])}",
            f"- coding_rules_items: {len(buckets['coding_rules'])}",
            f"- active_tasks_items: {len(buckets['active_tasks'])}",
            "",
        ]
    )
    changelog_path.write_text(changelog_body, encoding="utf-8")

    return CanonicalSummary(
        architecture_items=len(buckets["architecture"]),
        coding_rules_items=len(buckets["coding_rules"]),
        active_tasks_items=len(buckets["active_tasks"]),
        changelog_path=changelog_path.as_posix(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed canonical memory from generated memory/rlm_memory and run consolidation."
    )
    parser.add_argument("--project-root", required=True, help="Target project root path")
    parser.add_argument("--memory-dir", default="memory", help="Memory folder relative to project root")
    parser.add_argument("--max-items-per-file", type=int, default=6, help="Maximum extracted items per markdown file")
    parser.add_argument("--session-tag", default="bootstrap_seed", help="Tag appended to source for seeded facts")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    memory_dir = (project_root / args.memory_dir).resolve()
    rlm_root = memory_dir / "rlm_memory"
    log_path = memory_dir / "logs" / "extracted_facts.jsonl"

    if not rlm_root.exists():
        print(f"[seed-canonical] rlm_memory not found: {rlm_root.as_posix()}")
        return 2

    facts = _to_seed_facts(rlm_root, max_items_per_file=max(1, args.max_items_per_file))
    written = _append_extracted_facts(log_path, facts, session_tag=args.session_tag)

    consolidation = _write_canonical_from_log(memory_dir=memory_dir, log_rel_path="logs/extracted_facts.jsonl")

    print("[seed-canonical] completed")
    print(f"project_root={project_root.as_posix()}")
    print(f"memory_dir={memory_dir.as_posix()}")
    print(f"rlm_memory_dir={rlm_root.as_posix()}")
    print(f"seeded_facts={written}")
    print(f"canonical_architecture_items={consolidation.architecture_items}")
    print(f"canonical_coding_rules_items={consolidation.coding_rules_items}")
    print(f"canonical_active_tasks_items={consolidation.active_tasks_items}")
    print(f"changelog_path={consolidation.changelog_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
