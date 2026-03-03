from __future__ import annotations

import os
from datetime import datetime, timezone, tzinfo


ALLOWED_TIMESTAMP_MODES = {"local", "utc"}


def resolve_timestamp_mode(value: str | None) -> str:
    mode = (value or "local").strip().lower()
    return mode if mode in ALLOWED_TIMESTAMP_MODES else "local"


DEFAULT_TIMESTAMP_MODE = resolve_timestamp_mode(os.getenv("RLM_TIMESTAMP_MODE", "local"))


def current_timezone(mode: str | None = None) -> tzinfo:
    resolved = resolve_timestamp_mode(mode or DEFAULT_TIMESTAMP_MODE)
    if resolved == "utc":
        return timezone.utc
    return datetime.now().astimezone().tzinfo or timezone.utc


def now_dt(mode: str | None = None) -> datetime:
    resolved = resolve_timestamp_mode(mode or DEFAULT_TIMESTAMP_MODE)
    if resolved == "utc":
        return datetime.now(timezone.utc)
    return datetime.now().astimezone()


def now_iso(mode: str | None = None) -> str:
    return now_dt(mode).isoformat()
