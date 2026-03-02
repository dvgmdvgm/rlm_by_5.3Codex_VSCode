from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


MD_HEADER_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
IGNORED_PREFIXES = ("_archive/",)


@dataclass
class MemoryFileMeta:
    name: str
    path: str
    chars: int
    lines: int
    headers: list[str]


class MemoryStore:
    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir

    def ensure_dir(self) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _read_text_with_fallback(file_path: Path) -> str | None:
        encodings = ("utf-8", "utf-8-sig", "cp1251")
        for enc in encodings:
            try:
                return file_path.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
            except OSError:
                return None

        try:
            return file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def load_memory_context(self) -> dict[str, str]:
        self.ensure_dir()
        context: dict[str, str] = {}

        for file_path in sorted(self.memory_dir.glob("**/*")):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in {".md", ".txt", ".json", ".jsonl"}:
                continue
            rel = file_path.relative_to(self.memory_dir).as_posix()
            if rel.startswith(IGNORED_PREFIXES):
                continue
            text = self._read_text_with_fallback(file_path)
            if text is None:
                continue
            context[rel] = text

        return context

    def get_metadata(self) -> list[MemoryFileMeta]:
        self.ensure_dir()
        result: list[MemoryFileMeta] = []

        for file_path in sorted(self.memory_dir.glob("**/*")):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in {".md", ".txt", ".json", ".jsonl"}:
                continue

            rel = file_path.relative_to(self.memory_dir).as_posix()
            if rel.startswith(IGNORED_PREFIXES):
                continue

            text = self._read_text_with_fallback(file_path)
            if text is None:
                continue
            headers = MD_HEADER_RE.findall(text) if file_path.suffix.lower() == ".md" else []
            result.append(
                MemoryFileMeta(
                    name=file_path.name,
                    path=rel,
                    chars=len(text),
                    lines=text.count("\n") + 1 if text else 0,
                    headers=headers,
                )
            )

        return result
