from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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
    memory_mutation_mode: str



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
        memory_mutation_mode=os.getenv("RLM_MEMORY_MUTATION_MODE", "off").strip().lower(),
    )
