from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .time_policy import resolve_timestamp_mode


@dataclass(frozen=True)
class Settings:
    memory_dir: Path
    ollama_url: str
    ollama_model: str
    ollama_timeout: float
    max_concurrency: int
    trace_preview_chars: int
    trace_persist: bool
    trace_file: Path
    local_iter_log_enabled: bool
    local_iter_log_file: Path
    local_iter_log_preview_chars: int
    local_llm_force_english: bool
    timestamp_mode: str
    memory_mutation_mode: str
    cloud_payload_audit_auto_archive: bool
    cloud_payload_audit_max_lines: int
    cloud_payload_audit_archive_dir_name: str
    # --- Gemma 4 best-practices ---
    llm_temperature: float = 1.0
    llm_top_p: float = 0.95
    llm_top_k: int = 64
    llm_thinking_mode: bool = True



def load_settings() -> Settings:
    root = Path.cwd()
    memory_dir = Path(os.getenv("RLM_MEMORY_DIR", root / "memory"))
    trace_file_default = memory_dir / "logs" / "llm_trace.jsonl"
    local_iter_file_default = memory_dir / "logs" / "local_llm_iterations.log"

    return Settings(
        memory_dir=memory_dir,
        ollama_url=os.getenv("RLM_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
        ollama_model=os.getenv("RLM_OLLAMA_MODEL", "qwen2.5-coder:14b"),
        ollama_timeout=float(os.getenv("RLM_OLLAMA_TIMEOUT", "120")),
        max_concurrency=int(os.getenv("RLM_MAX_CONCURRENCY", "6")),
        trace_preview_chars=int(os.getenv("RLM_TRACE_PREVIEW_CHARS", "280")),
        trace_persist=os.getenv("RLM_TRACE_PERSIST", "false").lower() in {"1", "true", "yes", "on"},
        trace_file=Path(os.getenv("RLM_TRACE_FILE", str(trace_file_default))),
        local_iter_log_enabled=os.getenv("RLM_LOCAL_ITER_LOG_ENABLED", "true").lower() in {"1", "true", "yes", "on"},
        local_iter_log_file=Path(os.getenv("RLM_LOCAL_ITER_LOG_FILE", str(local_iter_file_default))),
        local_iter_log_preview_chars=int(os.getenv("RLM_LOCAL_ITER_LOG_PREVIEW_CHARS", "420")),
        local_llm_force_english=os.getenv("RLM_LOCAL_LLM_FORCE_ENGLISH", "true").lower() in {"1", "true", "yes", "on"},
        timestamp_mode=resolve_timestamp_mode(os.getenv("RLM_TIMESTAMP_MODE", "local")),
        memory_mutation_mode="on",  # Globally enabled regardless of ENV
        cloud_payload_audit_auto_archive=os.getenv("RLM_CLOUD_PAYLOAD_AUDIT_AUTO_ARCHIVE", "true").lower() in {"1", "true", "yes", "on"},
        cloud_payload_audit_max_lines=max(500, int(os.getenv("RLM_CLOUD_PAYLOAD_AUDIT_MAX_LINES", "20000"))),
        cloud_payload_audit_archive_dir_name=os.getenv("RLM_CLOUD_PAYLOAD_AUDIT_ARCHIVE_DIR", "cloud_payload_audit"),
        # Gemma 4 sampling & thinking
        llm_temperature=float(os.getenv("RLM_LLM_TEMPERATURE", "1.0")),
        llm_top_p=float(os.getenv("RLM_LLM_TOP_P", "0.95")),
        llm_top_k=int(os.getenv("RLM_LLM_TOP_K", "64")),
        llm_thinking_mode=os.getenv("RLM_LLM_THINKING_MODE", "true").lower() in {"1", "true", "yes", "on"},
    )
