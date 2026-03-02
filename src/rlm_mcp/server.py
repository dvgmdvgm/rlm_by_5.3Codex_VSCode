from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import re
import json
from datetime import datetime, timedelta, timezone

from mcp.server.fastmcp import FastMCP

from .config import load_settings
from .consolidator import consolidate_memory as consolidate_memory_impl
from .llm_adapter import OllamaAdapter
from .memory_store import MemoryStore
from .repl_runtime import ReplRuntime

settings = load_settings()
llm_adapter = OllamaAdapter(
    base_url=settings.ollama_url,
    model=settings.ollama_model,
    timeout=settings.ollama_timeout,
    default_max_concurrency=settings.max_concurrency,
)
runtimes: dict[str, ReplRuntime] = {}
stores: dict[str, MemoryStore] = {}

mcp = FastMCP("hybrid-rlm-memory")
CLOUD_PAYLOAD_LOG_REL_PATH = "logs/cloud_payload_audit.md"
CLOUD_PAYLOAD_SNAPSHOT_REL_PATH = "logs/cloud_payload_current.md"
CLOUD_PAYLOAD_PREVIEW_CHARS = 1200


def _resolve_memory_dir(project_path: str | None) -> Path:
    if project_path:
        return Path(project_path) / "memory"
    return settings.memory_dir


def _key(memory_dir: Path) -> str:
    return memory_dir.resolve().as_posix()


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def _truncate_text(value: str, limit: int = CLOUD_PAYLOAD_PREVIEW_CHARS) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + " ...<truncated>"


def _compact_preview(value):
    if isinstance(value, str):
        return _truncate_text(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        preview_items = [_compact_preview(item) for item in value[:6]]
        if len(value) > 6:
            preview_items.append(f"... +{len(value) - 6} more")
        return preview_items
    if isinstance(value, dict):
        preview: dict[str, object] = {}
        for index, key in enumerate(sorted(value.keys())):
            if index >= 12:
                preview["__truncated_keys__"] = f"+{len(value) - 12} keys"
                break
            preview[key] = _compact_preview(value[key])
        return preview
    return _truncate_text(str(value))


def _log_cloud_payload(
    *,
    tool_name: str,
    project_path: str | None,
    memory_dir: Path,
    payload: dict,
) -> None:
    log_path = memory_dir / CLOUD_PAYLOAD_LOG_REL_PATH
    snapshot_path = memory_dir / CLOUD_PAYLOAD_SNAPSHOT_REL_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    serialized = json.dumps(payload, ensure_ascii=False, default=str)
    payload_preview = _compact_preview(payload)
    timestamp = datetime.now(timezone.utc).isoformat()
    payload_keys = ", ".join(sorted(payload.keys()))
    preview_text = json.dumps(payload_preview, ensure_ascii=False, indent=2)
    project_value = project_path or "<none>"
    block = "\n".join(
        [
            "---",
            f"ts: {timestamp}",
            f"tool: {tool_name}",
            f"project_path: {project_value}",
            f"memory_dir: {memory_dir.as_posix()}",
            f"payload_chars: {len(serialized)}",
            f"payload_est_tokens: {_estimate_tokens(serialized)}",
            f"payload_keys: {payload_keys}",
            "payload_preview:",
            "```json",
            preview_text,
            "```",
            "",
        ]
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(block)

    snapshot_header = "\n".join(
        [
            "# Current Cloud Payload Snapshot",
            "",
            "This file is overwritten on each payload transfer to cloud-facing response channel.",
            "",
        ]
    )
    snapshot_path.write_text(snapshot_header + block, encoding="utf-8")


def _get_store(memory_dir: Path) -> MemoryStore:
    cache_key = _key(memory_dir)
    if cache_key not in stores:
        stores[cache_key] = MemoryStore(memory_dir)
    return stores[cache_key]


def _get_runtime(memory_dir: Path) -> ReplRuntime:
    cache_key = _key(memory_dir)
    if cache_key not in runtimes:
        store = _get_store(memory_dir)
        memory_context = store.load_memory_context()
        runtime = ReplRuntime(
            memory_context=memory_context,
            llm_adapter=llm_adapter,
            trace_preview_chars=settings.trace_preview_chars,
            trace_persist=settings.trace_persist,
            trace_file=memory_dir / "logs" / "llm_trace.jsonl",
            local_iter_log_enabled=settings.local_iter_log_enabled,
            local_iter_log_file=memory_dir / "logs" / "local_llm_iterations.log",
            local_iter_log_preview_chars=settings.local_iter_log_preview_chars,
            local_llm_force_english=settings.local_llm_force_english,
        )
        runtimes[cache_key] = runtime
    return runtimes[cache_key]


def _tokenize_query(text: str) -> set[str]:
    return {part for part in re.findall(r"[a-zA-Zа-яА-Я0-9_]+", text.lower()) if len(part) > 2}


def _get_preference_text(memory_context: dict[str, str], *paths: str) -> str:
    for path in paths:
        text = memory_context.get(path, "")
        if text.strip():
            return text
    return ""


def _infer_user_response_language(memory_context: dict[str, str]) -> str:
    communication_text = _get_preference_text(
        memory_context,
        "rlm_memory/13_preferences/communication.md",
        "canonical/communication.md",
    )
    language_text = _get_preference_text(
        memory_context,
        "rlm_memory/13_preferences/language_local.md",
        "rlm_memory/13_preferences/language.md",
        "canonical/language.md",
    )
    coding_rules_text = memory_context.get("canonical/coding_rules.md", "")

    explicit_comm_lang = re.search(
        r"(?m)^(?!\s*#)\s*COMMUNICATION_LANGUAGE\s*:\s*([a-zA-Z\-]+)\s*$",
        language_text,
        flags=re.IGNORECASE,
    )
    if explicit_comm_lang:
        code = explicit_comm_lang.group(1).strip().lower()
        if code in {"ru", "en", "uk", "es", "de", "fr", "ja", "pt", "it", "ko", "zh-cn"}:
            return code

    merged_text = (communication_text + "\n\n" + coding_rules_text).lower()

    explicit_lang = re.search(
        r"(?:user_response_language|response_language|language|lang)\s*[:=]\s*(ru|en)\b",
        merged_text,
        flags=re.IGNORECASE,
    )
    if explicit_lang:
        return explicit_lang.group(1).lower()

    communication_lower = communication_text.lower()

    ru_chat_patterns = [
        r"use\s+russian\s+language\s+for\s*:\s*[\s\S]{0,500}?all response text in the chat",
        r"all response text in the chat[\s\S]{0,200}?russian",
        r"ответ[а-я\s]{0,30}на русском",
    ]
    en_chat_patterns = [
        r"use\s+english\s+language\s+for\s*:\s*[\s\S]{0,500}?all response text in the chat",
        r"all response text in the chat[\s\S]{0,200}?english",
        r"ответ[а-я\s]{0,30}на англий",
    ]

    for pattern in ru_chat_patterns:
        if re.search(pattern, communication_lower, flags=re.IGNORECASE):
            return "ru"
    for pattern in en_chat_patterns:
        if re.search(pattern, communication_lower, flags=re.IGNORECASE):
            return "en"

    ru_terms = ["рус", "russian", "на русском", "language: ru", "lang: ru"]
    en_terms = ["english", "на англий", "language: en", "lang: en"]

    ru_pos = max((communication_lower.rfind(term) for term in ru_terms), default=-1)
    en_pos = max((communication_lower.rfind(term) for term in en_terms), default=-1)
    if ru_pos == -1 and en_pos == -1:
        return "auto"
    if ru_pos > en_pos:
        return "ru"
    return "en"


def _infer_user_response_style(memory_context: dict[str, str]) -> dict[str, str]:
    communication_path = "rlm_memory/13_preferences/communication.md"
    communication_text = memory_context.get(communication_path, "")
    if not communication_text.strip():
        communication_path = "canonical/communication.md"
        communication_text = memory_context.get(communication_path, "")

    if not communication_text.strip():
        return {
            "style": "default",
            "style_source": "none",
            "style_hint": "Use concise, structured responses.",
        }

    lowered = communication_text.lower()
    prefer_tables = "table" in lowered or "tables" in lowered
    prefer_emoji_headers = "emoji" in lowered and "header" in lowered
    prefer_structure = "clear structure" in lowered or "standard response pattern" in lowered

    hint_parts: list[str] = []
    if prefer_structure:
        hint_parts.append("structured sections")
    if prefer_tables:
        hint_parts.append("tables for comparisons/status")
    if prefer_emoji_headers:
        hint_parts.append("emoji section headers")
    if not hint_parts:
        hint_parts.append("clear and scannable style")

    return {
        "style": "preferences_based",
        "style_source": communication_path,
        "style_hint": "Use " + ", ".join(hint_parts) + ".",
    }


CHANGELOG_NAME_RE = re.compile(r"^rlm_consolidation_(\d{8})_(\d{6})\.md$")


def _parse_changelog_ts(name: str) -> datetime | None:
    match = CHANGELOG_NAME_RE.match(name)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1) + match.group(2), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _auto_summarize_old_changelogs(
    *,
    memory_dir: Path,
    older_than_days: int,
    keep_raw: bool,
    max_files_per_summary: int,
) -> dict:
    changelog_dir = memory_dir / "changelog"
    if not changelog_dir.exists():
        return {
            "summarization_enabled": True,
            "summaries_created": 0,
            "raw_files_summarized": 0,
            "raw_files_archived": 0,
        }

    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, older_than_days))
    candidates: list[tuple[Path, datetime]] = []
    for path in sorted(changelog_dir.glob("rlm_consolidation_*.md")):
        ts = _parse_changelog_ts(path.name)
        if not ts:
            continue
        if ts >= cutoff:
            continue
        candidates.append((path, ts))

    if not candidates:
        return {
            "summarization_enabled": True,
            "summaries_created": 0,
            "raw_files_summarized": 0,
            "raw_files_archived": 0,
        }

    summaries_dir = changelog_dir / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    archive_dir = memory_dir / "_archive" / "changelog_raw"
    archive_dir.mkdir(parents=True, exist_ok=True)

    by_month: dict[str, list[Path]] = {}
    for path, ts in candidates:
        key = ts.strftime("%Y-%m")
        by_month.setdefault(key, []).append(path)

    summaries_created = 0
    raw_files_summarized = 0
    raw_files_archived = 0

    for month, files in sorted(by_month.items()):
        chunks: list[list[Path]] = []
        for index in range(0, len(files), max(1, max_files_per_summary)):
            chunks.append(files[index:index + max(1, max_files_per_summary)])

        for chunk_index, chunk_files in enumerate(chunks, start=1):
            combined = []
            for path in chunk_files:
                text = path.read_text(encoding="utf-8", errors="replace")
                combined.append(f"## SOURCE_FILE: {path.name}\n{text[:12000]}")

            prompt = (
                "You are a local memory summarizer. Respond in English only. "
                "Summarize the changelog inputs into concise bullet points with sections: "
                "Key Changes, Rules/Policies, Risks/Follow-ups.\n\n"
                f"MONTH: {month}\n"
                f"FILES: {', '.join(path.name for path in chunk_files)}\n\n"
                "CHANGELOG INPUTS:\n"
                + "\n\n".join(combined)
            )
            summary = llm_adapter.query(prompt)

            suffix = f"_{chunk_index:02d}" if len(chunks) > 1 else ""
            out_path = summaries_dir / f"rlm_monthly_summary_{month.replace('-', '')}{suffix}.md"
            body = "\n".join(
                [
                    f"# RLM Monthly Changelog Summary ({month})",
                    "",
                    "## META",
                    f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
                    "- generator: local_llm",
                    f"- source_files: {len(chunk_files)}",
                    f"- keep_raw: {keep_raw}",
                    "",
                    "## Sources",
                    *[f"- {path.name}" for path in chunk_files],
                    "",
                    "## Summary",
                    summary.strip(),
                    "",
                ]
            )
            out_path.write_text(body, encoding="utf-8")
            summaries_created += 1
            raw_files_summarized += len(chunk_files)

            if not keep_raw:
                for path in chunk_files:
                    destination = archive_dir / path.name
                    path.replace(destination)
                    raw_files_archived += 1

    return {
        "summarization_enabled": True,
        "summaries_created": summaries_created,
        "raw_files_summarized": raw_files_summarized,
        "raw_files_archived": raw_files_archived,
    }


@mcp.tool()
def execute_repl_code(code: str, project_path: str | None = None) -> dict:
    """Execute Python code in a stateful REPL and return stdout/stderr/errors/final answer."""
    memory_dir = _resolve_memory_dir(project_path)
    runtime = _get_runtime(memory_dir)
    result = runtime.execute(code)
    response = {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "error": result.error,
        "final": result.final,
        "llm_trace": result.llm_trace,
        "project_path": project_path,
        "memory_dir": memory_dir.as_posix(),
    }
    _log_cloud_payload(
        tool_name="execute_repl_code",
        project_path=project_path,
        memory_dir=memory_dir,
        payload=response,
    )
    return response


@mcp.tool()
def get_memory_metadata(
    project_path: str | None = None,
    max_files: int = 20,
    include_headers: bool = False,
    include_files: bool = False,
    sort_by: str = "chars_desc",
) -> dict:
    """Return lightweight metadata about memory files without full-text transfer."""
    memory_dir = _resolve_memory_dir(project_path)
    memory_store = _get_store(memory_dir)
    raw_items = memory_store.get_metadata()
    total_files = len(raw_items)
    total_chars = sum(item.chars for item in raw_items)
    total_lines = sum(item.lines for item in raw_items)

    if sort_by == "chars_desc":
        raw_items.sort(key=lambda item: item.chars, reverse=True)
    elif sort_by == "chars_asc":
        raw_items.sort(key=lambda item: item.chars)
    else:
        raw_items.sort(key=lambda item: item.path)

    limit = max(0, max_files)
    limited_items = raw_items[:limit] if include_files else []
    metadata = [asdict(item) for item in limited_items]
    if not include_headers:
        for item in metadata:
            item.pop("headers", None)

    response = {
        "memory_dir": memory_dir.as_posix(),
        "files": metadata,
        "count": len(metadata),
        "total_files": total_files,
        "total_chars": total_chars,
        "total_lines": total_lines,
        "truncated": include_files and total_files > len(metadata),
        "options": {
            "max_files": limit,
            "include_headers": include_headers,
            "include_files": include_files,
            "sort_by": sort_by,
        },
        "project_path": project_path,
    }
    _log_cloud_payload(
        tool_name="get_memory_metadata",
        project_path=project_path,
        memory_dir=memory_dir,
        payload=response,
    )
    return response


@mcp.tool()
def local_memory_brief(
    question: str,
    project_path: str | None = None,
    max_files: int = 8,
    max_chars_per_file: int = 3500,
) -> dict:
    """Build a compact answer from memory using local model only, returning concise brief + selected files."""
    memory_dir = _resolve_memory_dir(project_path)
    memory_store = _get_store(memory_dir)
    memory_context = memory_store.load_memory_context()

    terms = _tokenize_query(question)
    scored: list[tuple[int, str, str]] = []
    preferred_prefixes = (
        "canonical/",
        "rlm_memory/",
    )

    for path, text in memory_context.items():
        base_score = 0
        lower_path = path.lower()
        lower_text = text.lower()

        if lower_path.startswith(preferred_prefixes):
            base_score += 3

        if terms:
            hit_count = sum(1 for term in terms if term in lower_path or term in lower_text)
            base_score += hit_count

        if base_score <= 0:
            continue

        scored.append((base_score, path, text[:max_chars_per_file]))

    scored.sort(key=lambda row: (-row[0], row[1]))
    selected = scored[: max(1, max_files)]
    snippets = "\n\n".join(
        f"### FILE: {path}\n{snippet}" for _, path, snippet in selected
    )

    prompt = (
        "You are the project's local memory model. Use only the memory context below. "
        "Respond in English only. "
        "Give a short factual answer in 3-6 bullet points. "
        "If memory sources conflict, report the range and conflict source.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"MEMORY CONTEXT:\n{snippets}\n"
    )
    answer = llm_adapter.query(prompt)

    response = {
        "question": question,
        "brief": answer,
        "selected_files": [path for _, path, _ in selected],
        "selected_count": len(selected),
        "project_path": project_path,
        "memory_dir": memory_dir.as_posix(),
    }
    _log_cloud_payload(
        tool_name="local_memory_brief",
        project_path=project_path,
        memory_dir=memory_dir,
        payload=response,
    )
    return response


@mcp.tool()
def local_memory_bootstrap(
    question: str,
    project_path: str | None = None,
    max_files: int = 8,
    max_chars_per_file: int = 3500,
) -> dict:
    """Run local-first memory bootstrap: reload context + compact metadata + local brief in one call."""
    memory_dir = _resolve_memory_dir(project_path)
    memory_store = _get_store(memory_dir)
    runtime = _get_runtime(memory_dir)

    context = memory_store.load_memory_context()
    runtime.refresh_memory(context)
    user_response_language = _infer_user_response_language(context)
    user_response_style = _infer_user_response_style(context)

    metadata = get_memory_metadata(
        project_path=project_path,
        max_files=20,
        include_headers=False,
        include_files=False,
        sort_by="chars_desc",
    )
    brief = local_memory_brief(
        question=question,
        project_path=project_path,
        max_files=max_files,
        max_chars_per_file=max_chars_per_file,
    )

    response = {
        "question": question,
        "reloaded_files": len(context),
        "brief": brief["brief"],
        "selected_files": brief["selected_files"],
        "selected_count": brief["selected_count"],
        "local_model_output_language": "en",
        "user_response_language": user_response_language,
        "user_response_style": user_response_style,
        "memory_stats": {
            "total_files": metadata["total_files"],
            "total_chars": metadata["total_chars"],
            "total_lines": metadata["total_lines"],
        },
        "project_path": project_path,
        "memory_dir": memory_dir.as_posix(),
    }
    _log_cloud_payload(
        tool_name="local_memory_bootstrap",
        project_path=project_path,
        memory_dir=memory_dir,
        payload=response,
    )
    return response


@mcp.tool()
def reload_memory_context(project_path: str | None = None) -> dict:
    """Reload memory files into REPL global memory_context."""
    memory_dir = _resolve_memory_dir(project_path)
    memory_store = _get_store(memory_dir)
    runtime = _get_runtime(memory_dir)
    context = memory_store.load_memory_context()
    runtime.refresh_memory(context)
    response = {
        "files": len(context),
        "keys": sorted(context.keys()),
        "project_path": project_path,
        "memory_dir": memory_dir.as_posix(),
    }
    _log_cloud_payload(
        tool_name="reload_memory_context",
        project_path=project_path,
        memory_dir=memory_dir,
        payload=response,
    )
    return response


@mcp.tool()
def consolidate_memory(
    log_rel_path: str = "logs/extracted_facts.jsonl",
    write_changelog: bool = True,
    refresh_context: bool = True,
    project_path: str | None = None,
    summarize_old_changelogs: bool = True,
    older_than_days: int = 2,
    keep_raw_changelogs: bool = False,
    max_files_per_summary: int = 20,
) -> dict:
    """Consolidate extracted facts log into canonical memory files and optional changelog."""
    memory_dir = _resolve_memory_dir(project_path)
    memory_store = _get_store(memory_dir)
    runtime = _get_runtime(memory_dir)
    result = consolidate_memory_impl(
        memory_dir=memory_dir,
        log_rel_path=log_rel_path,
        write_changelog=write_changelog,
    )
    response = asdict(result)
    response["project_path"] = project_path
    response["memory_dir"] = memory_dir.as_posix()

    if summarize_old_changelogs:
        summary_stats = _auto_summarize_old_changelogs(
            memory_dir=memory_dir,
            older_than_days=older_than_days,
            keep_raw=keep_raw_changelogs,
            max_files_per_summary=max_files_per_summary,
        )
        response.update(summary_stats)
    else:
        response["summarization_enabled"] = False

    if refresh_context:
        context = memory_store.load_memory_context()
        runtime.refresh_memory(context)
        response["reloaded_files"] = len(context)

    _log_cloud_payload(
        tool_name="consolidate_memory",
        project_path=project_path,
        memory_dir=memory_dir,
        payload=response,
    )
    return response


def run() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
