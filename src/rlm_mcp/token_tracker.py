"""Token savings tracker — persistent analytics for output compression.

Records every compression event and provides gain/discover analytics.
Data stored as JSONL in memory/logs/token_savings.jsonl.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CompressionEvent:
    """One recorded compression event."""
    ts: str
    command: str
    command_type: str
    original_tokens: int
    compressed_tokens: int
    savings_pct: float
    strategies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TokenTracker:
    """Tracks token savings persistently in a JSONL file."""

    LOG_REL_PATH = "logs/token_savings.jsonl"

    def __init__(self, memory_dir: Path):
        self.log_path = memory_dir / self.LOG_REL_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: CompressionEvent) -> None:
        """Append compression event to log."""
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def _load_events(self) -> list[dict[str, Any]]:
        """Load all events from log."""
        if not self.log_path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in self.log_path.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return events

    def gain_summary(self) -> dict[str, Any]:
        """Calculate total token savings stats."""
        events = self._load_events()
        if not events:
            return {
                "total_commands": 0,
                "total_original_tokens": 0,
                "total_compressed_tokens": 0,
                "total_saved_tokens": 0,
                "average_savings_pct": 0.0,
                "by_type": {},
            }

        total_original = sum(e["original_tokens"] for e in events)
        total_compressed = sum(e["compressed_tokens"] for e in events)
        total_saved = total_original - total_compressed

        # Group by command_type
        by_type: dict[str, dict[str, int]] = {}
        for e in events:
            ct = e.get("command_type", "generic")
            if ct not in by_type:
                by_type[ct] = {"count": 0, "original": 0, "compressed": 0}
            by_type[ct]["count"] += 1
            by_type[ct]["original"] += e["original_tokens"]
            by_type[ct]["compressed"] += e["compressed_tokens"]

        for ct_data in by_type.values():
            orig = ct_data["original"]
            ct_data["savings_pct"] = round(
                (1 - ct_data["compressed"] / max(orig, 1)) * 100, 1
            )

        avg_pct = (1 - total_compressed / max(total_original, 1)) * 100

        return {
            "total_commands": len(events),
            "total_original_tokens": total_original,
            "total_compressed_tokens": total_compressed,
            "total_saved_tokens": total_saved,
            "average_savings_pct": round(avg_pct, 1),
            "by_type": by_type,
        }

    def recent_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent compression events."""
        events = self._load_events()
        return events[-limit:]
