"""Multi-language code indexer with symbol-level retrieval via tree-sitter.

Indexes a codebase once, then provides O(1) byte-offset retrieval of
individual symbols (functions, classes, methods, types, constants).
Falls back to Python built-in ``ast`` for .py files when tree-sitter
is unavailable.
"""

from __future__ import annotations

import ast as python_ast
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# ---------- optional tree-sitter imports ----------
_TS_AVAILABLE = False
_TS_LANGUAGE_LOADERS: dict[str, Any] = {}

try:
    from tree_sitter import Language as _TSLanguage, Parser as _TSParser

    # Individual language packages — each is optional
    _LANG_MODULES: list[tuple[str, str, str | None]] = [
        # (language_key, module_name, function_name_override)
        ("python", "tree_sitter_python", None),
        ("javascript", "tree_sitter_javascript", None),
        ("typescript", "tree_sitter_typescript", "language_typescript"),
        ("tsx", "tree_sitter_typescript", "language_tsx"),
        ("css", "tree_sitter_css", None),
        ("go", "tree_sitter_go", None),
        ("rust", "tree_sitter_rust", None),
        ("java", "tree_sitter_java", None),
        ("c_sharp", "tree_sitter_c_sharp", None),
        ("c", "tree_sitter_c", None),
        ("cpp", "tree_sitter_cpp", None),
        ("ruby", "tree_sitter_ruby", None),
    ]

    for _lang_key, _mod_name, _func_override in _LANG_MODULES:
        try:
            _mod = __import__(_mod_name)
            _func_name = _func_override or "language"
            _lang_func = getattr(_mod, _func_name, None)
            if _lang_func is not None:
                _TS_LANGUAGE_LOADERS[_lang_key] = _lang_func
        except ImportError:
            pass

    _TS_AVAILABLE = len(_TS_LANGUAGE_LOADERS) > 0
except ImportError:
    _TSLanguage = None  # type: ignore[assignment,misc]
    _TSParser = None  # type: ignore[assignment,misc]


# ================================================================
# Language configuration
# ================================================================

IGNORE_DIRS: set[str] = {
    ".git", ".idea", ".vscode", ".vs", "node_modules", "dist", "build",
    "coverage", "out", "target", "bin", "obj", ".venv", "venv",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".next", ".nuxt",
    ".turbo", ".cache", "DerivedData", "Pods", ".gradle", ".dart_tool",
    "env", ".egg-info", "rlm_memory_mcp.egg-info",
}

# (language_key, grammar_name, extensions, {node_type: symbol_kind})
LANG_CONFIG: dict[str, dict[str, Any]] = {
    "python": {
        "extensions": {".py"},
        "grammar": "python",
        "symbol_nodes": {
            "function_definition": "function",
            "class_definition": "class",
        },
    },
    "javascript": {
        "extensions": {".js", ".jsx", ".mjs"},
        "grammar": "javascript",
        "symbol_nodes": {
            "function_declaration": "function",
            "class_declaration": "class",
            "method_definition": "method",
        },
    },
    "typescript": {
        "extensions": {".ts"},
        "grammar": "typescript",
        "symbol_nodes": {
            "function_declaration": "function",
            "class_declaration": "class",
            "method_definition": "method",
            "interface_declaration": "type",
            "type_alias_declaration": "type",
            "enum_declaration": "type",
        },
    },
    "tsx": {
        "extensions": {".tsx"},
        "grammar": "tsx",
        "symbol_nodes": {
            "function_declaration": "function",
            "class_declaration": "class",
            "method_definition": "method",
            "interface_declaration": "type",
            "type_alias_declaration": "type",
            "enum_declaration": "type",
        },
    },
    "css": {
        "extensions": {".css"},
        "grammar": "css",
        "symbol_nodes": {
            "rule_set": "selector",
            "media_statement": "at-rule",
            "keyframes_statement": "at-rule",
        },
    },
    "go": {
        "extensions": {".go"},
        "grammar": "go",
        "symbol_nodes": {
            "function_declaration": "function",
            "method_declaration": "method",
            "type_declaration": "type",
        },
    },
    "rust": {
        "extensions": {".rs"},
        "grammar": "rust",
        "symbol_nodes": {
            "function_item": "function",
            "struct_item": "type",
            "enum_item": "type",
            "impl_item": "impl",
            "trait_item": "type",
        },
    },
    "java": {
        "extensions": {".java"},
        "grammar": "java",
        "symbol_nodes": {
            "class_declaration": "class",
            "method_declaration": "method",
            "interface_declaration": "type",
            "enum_declaration": "type",
        },
    },
    "c_sharp": {
        "extensions": {".cs"},
        "grammar": "c_sharp",
        "symbol_nodes": {
            "class_declaration": "class",
            "method_declaration": "method",
            "interface_declaration": "type",
            "struct_declaration": "type",
            "enum_declaration": "type",
        },
    },
    "c": {
        "extensions": {".c"},
        "grammar": "c",
        "symbol_nodes": {
            "function_definition": "function",
            "struct_specifier": "type",
            "enum_specifier": "type",
            "type_definition": "type",
        },
    },
    "cpp": {
        "extensions": {".cpp", ".cc", ".cxx", ".hpp", ".h"},
        "grammar": "cpp",
        "symbol_nodes": {
            "function_definition": "function",
            "class_specifier": "class",
            "struct_specifier": "type",
            "enum_specifier": "type",
        },
    },
    "ruby": {
        "extensions": {".rb", ".rake"},
        "grammar": "ruby",
        "symbol_nodes": {
            "class": "class",
            "method": "method",
            "singleton_method": "method",
            "module": "type",
        },
    },
    "kotlin": {
        "extensions": {".kt"},
        "grammar": "kotlin",
        "symbol_nodes": {
            "class_declaration": "class",
            "function_declaration": "function",
            "object_declaration": "class",
        },
    },
    "dart": {
        "extensions": {".dart"},
        "grammar": "dart",
        "symbol_nodes": {
            "class_definition": "class",
            "function_signature": "function",
            "method_signature": "method",
        },
    },
}

# Extension → language key lookup
_EXT_TO_LANG: dict[str, str] = {}
for _lang_name, _cfg in LANG_CONFIG.items():
    for _ext in _cfg["extensions"]:
        _EXT_TO_LANG[_ext] = _lang_name


# ================================================================
# Tree-sitter symbol extraction helpers
# ================================================================

def _read_bytes_safe(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        return b""


def _extract_name(node: Any, source_bytes: bytes, language: str) -> str:
    """Extract symbol name from a tree-sitter AST node."""
    # CSS: selector text or at-rule preamble
    if language in ("css", "scss"):
        if node.type == "rule_set":
            for child in node.children:
                if "selector" in child.type.lower():
                    txt = source_bytes[child.start_byte:child.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                    return txt.strip()[:80]
        txt = source_bytes[
            node.start_byte : min(node.start_byte + 80, node.end_byte)
        ].decode("utf-8", errors="replace")
        return txt.split("{")[0].strip()[:80]

    # Generic: find child nodes that carry the symbol name
    for child in node.children:
        if child.type in (
            "name",
            "identifier",
            "property_identifier",
            "type_identifier",
            "field_identifier",
        ):
            return source_bytes[child.start_byte : child.end_byte].decode(
                "utf-8", errors="replace"
            )

    # Fallback: first line text
    txt = source_bytes[
        node.start_byte : min(node.start_byte + 80, node.end_byte)
    ].decode("utf-8", errors="replace")
    first_line = txt.split("\n")[0].strip()
    return first_line[:60] or f"<{node.type}>"


def _extract_signature(source_bytes: bytes, start_byte: int, end_byte: int) -> str:
    """Extract compact human-readable signature from byte range."""
    chunk = source_bytes[start_byte : min(start_byte + 500, end_byte)].decode(
        "utf-8", errors="replace"
    )
    lines = chunk.split("\n")
    sig_parts = [lines[0].rstrip()]
    for line in lines[1:4]:
        stripped = line.rstrip()
        if not stripped:
            break
        sig_parts.append(stripped)
        if stripped.endswith((":", "{", ";", ")")):
            break
    return " ".join(sig_parts)[:200]


def _walk_tree(
    node: Any,
    source_bytes: bytes,
    language: str,
    symbol_nodes: dict[str, str],
    symbols: list[dict[str, Any]],
    file_rel_path: str,
    class_stack: list[str] | None = None,
) -> None:
    """Recursively walk tree-sitter AST and collect symbols."""
    if class_stack is None:
        class_stack = []

    matched_kind = symbol_nodes.get(node.type)

    if matched_kind is not None:
        name = _extract_name(node, source_bytes, language)
        kind = matched_kind
        # A function inside a class context → method
        if kind == "function" and class_stack:
            kind = "method"

        qualified_name = ".".join(class_stack + [name]) if class_stack else name
        symbol_id = f"{file_rel_path}::{qualified_name}#{kind}"
        signature = _extract_signature(source_bytes, node.start_byte, node.end_byte)

        symbols.append(
            {
                "symbol_id": symbol_id,
                "name": name,
                "qualified_name": qualified_name,
                "kind": kind,
                "file_path": file_rel_path,
                "language": language,
                "signature": signature,
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "chars": node.end_byte - node.start_byte,
            }
        )

        # Push class scope for children
        if kind == "class":
            class_stack = class_stack + [name]

    for child in node.children:
        _walk_tree(
            child, source_bytes, language, symbol_nodes, symbols,
            file_rel_path, class_stack,
        )


def _extract_arrow_functions(
    node: Any,
    source_bytes: bytes,
    language: str,
    symbols: list[dict[str, Any]],
    file_rel_path: str,
    class_stack: list[str] | None = None,
) -> None:
    """Handle JS/TS arrow functions assigned to const/let/var."""
    if class_stack is None:
        class_stack = []

    if node.type in ("variable_declaration", "lexical_declaration"):
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = None
                has_arrow = False
                for vc in child.children:
                    if vc.type in ("identifier", "name"):
                        name_node = vc
                    if vc.type == "arrow_function":
                        has_arrow = True
                if name_node and has_arrow:
                    name = source_bytes[
                        name_node.start_byte : name_node.end_byte
                    ].decode("utf-8", errors="replace")
                    kind = "method" if class_stack else "function"
                    qualified_name = (
                        ".".join(class_stack + [name]) if class_stack else name
                    )
                    symbol_id = f"{file_rel_path}::{qualified_name}#{kind}"
                    signature = _extract_signature(
                        source_bytes, node.start_byte, node.end_byte,
                    )
                    symbols.append(
                        {
                            "symbol_id": symbol_id,
                            "name": name,
                            "qualified_name": qualified_name,
                            "kind": kind,
                            "file_path": file_rel_path,
                            "language": language,
                            "signature": signature,
                            "start_byte": node.start_byte,
                            "end_byte": node.end_byte,
                            "start_line": node.start_point[0] + 1,
                            "end_line": node.end_point[0] + 1,
                            "chars": node.end_byte - node.start_byte,
                        }
                    )

    for child in node.children:
        _extract_arrow_functions(
            child, source_bytes, language, symbols, file_rel_path, class_stack,
        )


# ================================================================
# Python ast fallback
# ================================================================

def _line_byte_offsets(source_text: str) -> list[int]:
    """Return byte offset of each 1-indexed line start."""
    encoded = source_text.encode("utf-8")
    offsets = [0]
    for i, b in enumerate(encoded):
        if b == ord("\n"):
            offsets.append(i + 1)
    return offsets


def _python_ast_extract(source_text: str, file_rel_path: str) -> list[dict[str, Any]]:
    """Extract Python symbols using the built-in ast module (no deps)."""
    try:
        tree = python_ast.parse(source_text, filename=file_rel_path)
    except SyntaxError:
        return []

    offsets = _line_byte_offsets(source_text)
    source_len = len(source_text.encode("utf-8"))
    lines = source_text.split("\n")
    symbols: list[dict[str, Any]] = []

    def _byte(lineno: int) -> int:
        idx = lineno - 1
        if 0 <= idx < len(offsets):
            return offsets[idx]
        return source_len

    def _visit(node: python_ast.AST, class_stack: list[str]) -> None:
        if isinstance(node, (python_ast.FunctionDef, python_ast.AsyncFunctionDef)):
            kind = "method" if class_stack else "function"
            name = node.name
            qualified_name = ".".join(class_stack + [name]) if class_stack else name
            symbol_id = f"{file_rel_path}::{qualified_name}#{kind}"
            sig = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else name
            start_line = node.lineno
            end_line = node.end_lineno or node.lineno
            sb = _byte(start_line)
            eb = _byte(end_line + 1) if end_line < len(offsets) else source_len
            symbols.append(
                {
                    "symbol_id": symbol_id,
                    "name": name,
                    "qualified_name": qualified_name,
                    "kind": kind,
                    "file_path": file_rel_path,
                    "language": "python",
                    "signature": sig[:200],
                    "start_byte": sb,
                    "end_byte": eb,
                    "start_line": start_line,
                    "end_line": end_line,
                    "chars": eb - sb,
                }
            )
            for child in python_ast.iter_child_nodes(node):
                _visit(child, class_stack)

        elif isinstance(node, python_ast.ClassDef):
            name = node.name
            qualified_name = ".".join(class_stack + [name]) if class_stack else name
            symbol_id = f"{file_rel_path}::{qualified_name}#class"
            sig = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else f"class {name}"
            start_line = node.lineno
            end_line = node.end_lineno or node.lineno
            sb = _byte(start_line)
            eb = _byte(end_line + 1) if end_line < len(offsets) else source_len
            symbols.append(
                {
                    "symbol_id": symbol_id,
                    "name": name,
                    "qualified_name": qualified_name,
                    "kind": "class",
                    "file_path": file_rel_path,
                    "language": "python",
                    "signature": sig[:200],
                    "start_byte": sb,
                    "end_byte": eb,
                    "start_line": start_line,
                    "end_line": end_line,
                    "chars": eb - sb,
                }
            )
            for child in python_ast.iter_child_nodes(node):
                _visit(child, class_stack + [name])

        else:
            for child in python_ast.iter_child_nodes(node):
                _visit(child, class_stack)

    for top in python_ast.iter_child_nodes(tree):
        _visit(top, [])

    return symbols


# ================================================================
# CodeIndex — main class
# ================================================================


class CodeIndex:
    """Multi-language code index with symbol-level retrieval."""

    def __init__(self, project_root: Path, index_dir: Path) -> None:
        self.project_root = project_root.resolve()
        self.index_dir = index_dir
        self.index_path = index_dir / "index.json"
        self._index: dict[str, Any] | None = None
        self._parsers: dict[str, Any] = {}
        self._available_grammars: set[str] = set()
        self._init_parsers()

    # ---------- parser setup ----------

    def _init_parsers(self) -> None:
        if not _TS_AVAILABLE or _TSParser is None or _TSLanguage is None:
            return
        for lang_name in LANG_CONFIG:
            loader = _TS_LANGUAGE_LOADERS.get(lang_name)
            if loader is None:
                continue
            try:
                lang_ptr = loader()
                language = _TSLanguage(lang_ptr)
                parser = _TSParser(language)
                self._parsers[lang_name] = parser
                self._available_grammars.add(lang_name)
            except Exception:
                pass  # language package not installed or incompatible

    # ---------- indexing ----------

    def index_project(
        self,
        max_files: int = 500,
        max_file_bytes: int = 500_000,
    ) -> dict[str, Any]:
        """Walk project tree, parse files, build symbol index."""
        symbols: list[dict[str, Any]] = []
        files_indexed = 0
        files_skipped = 0
        total_source_bytes = 0
        lang_file_counts: dict[str, int] = {}
        lang_symbol_counts: dict[str, int] = {}

        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            dirs[:] = [
                d for d in dirs
                if d not in IGNORE_DIRS and not (d.startswith(".") and d != ".github")
            ]

            for fname in sorted(files):
                if files_indexed >= max_files:
                    break

                file_path = root_path / fname
                suffix = file_path.suffix.lower()
                language = _EXT_TO_LANG.get(suffix)
                if language is None:
                    continue

                rel_path = file_path.relative_to(self.project_root).as_posix()
                # Skip non-source directories
                if rel_path.startswith(("memory/", ".git/")):
                    files_skipped += 1
                    continue

                source_bytes = _read_bytes_safe(file_path)
                if not source_bytes or len(source_bytes) > max_file_bytes:
                    files_skipped += 1
                    continue

                file_symbols = self._extract_symbols(source_bytes, rel_path, language)
                symbols.extend(file_symbols)
                total_source_bytes += len(source_bytes)
                files_indexed += 1
                lang_file_counts[language] = lang_file_counts.get(language, 0) + 1
                lang_symbol_counts[language] = (
                    lang_symbol_counts.get(language, 0) + len(file_symbols)
                )

            if files_indexed >= max_files:
                break

        index_data: dict[str, Any] = {
            "version": 1,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "project_root": self.project_root.as_posix(),
            "stats": {
                "total_files": files_indexed,
                "files_skipped": files_skipped,
                "total_symbols": len(symbols),
                "total_source_bytes": total_source_bytes,
                "total_source_tokens_est": max(1, total_source_bytes // 4),
                "languages_files": lang_file_counts,
                "languages_symbols": lang_symbol_counts,
                "tree_sitter_available": _TS_AVAILABLE,
                "grammars_loaded": sorted(self._available_grammars),
            },
            "symbols": symbols,
        }

        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(
            json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        self._index = index_data

        return {
            "ok": True,
            "total_files": files_indexed,
            "total_symbols": len(symbols),
            "total_source_bytes": total_source_bytes,
            "total_source_tokens_est": max(1, total_source_bytes // 4),
            "languages_files": lang_file_counts,
            "languages_symbols": lang_symbol_counts,
            "tree_sitter": _TS_AVAILABLE,
            "grammars_loaded": sorted(self._available_grammars),
            "index_path": self.index_path.as_posix(),
        }

    def _extract_symbols(
        self,
        source_bytes: bytes,
        file_rel_path: str,
        language: str,
    ) -> list[dict[str, Any]]:
        cfg = LANG_CONFIG.get(language, {})
        symbol_nodes: dict[str, str] = cfg.get("symbol_nodes", {})

        # tree-sitter path
        if language in self._parsers:
            parser = self._parsers[language]
            try:
                tree = parser.parse(source_bytes)
                symbols: list[dict[str, Any]] = []
                _walk_tree(
                    tree.root_node, source_bytes, language,
                    symbol_nodes, symbols, file_rel_path,
                )
                # JS/TS arrow functions
                if language in ("javascript", "typescript", "tsx"):
                    _extract_arrow_functions(
                        tree.root_node, source_bytes, language,
                        symbols, file_rel_path,
                    )
                return symbols
            except Exception:
                pass  # fall through

        # Python fallback via built-in ast
        if language == "python":
            try:
                source_text = source_bytes.decode("utf-8", errors="replace")
                return _python_ast_extract(source_text, file_rel_path)
            except Exception:
                return []

        return []

    # ---------- search ----------

    def search_symbols(
        self,
        query: str,
        kind: str | None = None,
        language: str | None = None,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """Search indexed symbols by name, kind, or language."""
        index = self._load_index()
        if not index:
            return []

        query_lower = query.lower()
        results: list[dict[str, Any]] = []

        for sym in index["symbols"]:
            if kind and sym["kind"] != kind:
                continue
            if language and sym["language"] != language:
                continue

            name_lower = sym["name"].lower()
            qn_lower = sym["qualified_name"].lower()

            score = 0
            if name_lower == query_lower:
                score = 100
            elif qn_lower == query_lower:
                score = 95
            elif query_lower in name_lower:
                score = 80
            elif query_lower in qn_lower:
                score = 70
            elif query_lower in sym.get("signature", "").lower():
                score = 50

            if score > 0:
                results.append({**sym, "_score": score})

        results.sort(key=lambda x: (-x["_score"], x["name"]))
        for r in results[:max_results]:
            r.pop("_score", None)
        return results[:max_results]

    # ---------- retrieval ----------

    def get_symbol(self, symbol_id: str) -> dict[str, Any] | None:
        """Retrieve full symbol source via O(1) byte-offset seeking."""
        index = self._load_index()
        if not index:
            return None

        for sym in index["symbols"]:
            if sym["symbol_id"] == symbol_id:
                file_path = self.project_root / sym["file_path"]
                source_bytes = _read_bytes_safe(file_path)
                if not source_bytes:
                    return {**sym, "source": "<file not found>", "error": "file_not_found"}

                source = source_bytes[sym["start_byte"] : sym["end_byte"]].decode(
                    "utf-8", errors="replace",
                )
                return {
                    **sym,
                    "source": source,
                    "source_chars": len(source),
                    "source_tokens_est": max(1, len(source) // 4),
                }
        return None

    # ---------- file outline ----------

    def get_file_outline(self, file_path: str) -> list[dict[str, Any]]:
        """Return symbol outline for a specific file (no source bodies)."""
        index = self._load_index()
        if not index:
            return []

        compact_keys = (
            "symbol_id", "name", "qualified_name", "kind", "language",
            "signature", "start_line", "end_line", "chars",
        )
        return [
            {k: sym[k] for k in compact_keys if k in sym}
            for sym in index["symbols"]
            if sym["file_path"] == file_path
        ]

    # ---------- persistence ----------

    def _load_index(self) -> dict[str, Any] | None:
        if self._index is not None:
            return self._index
        if self.index_path.exists():
            try:
                self._index = json.loads(
                    self.index_path.read_text(encoding="utf-8"),
                )
                return self._index
            except Exception:
                return None
        return None

    # ---------- utility ----------

    def get_compact_summary(self) -> dict[str, Any] | None:
        """Return lightweight project code map suitable for bootstrap context."""
        index = self._load_index()
        if not index:
            return None
        stats = index.get("stats", {})
        file_counts: dict[str, int] = {}
        for sym in index.get("symbols", []):
            fp = sym["file_path"]
            file_counts[fp] = file_counts.get(fp, 0) + 1
        return {
            "indexed_at": index.get("indexed_at", ""),
            "total_files": stats.get("total_files", 0),
            "total_symbols": stats.get("total_symbols", 0),
            "total_source_tokens_est": stats.get("total_source_tokens_est", 0),
            "languages": stats.get("languages_files", {}),
            "files": file_counts,
            "hint": "Use search_code_symbols / get_code_symbol / get_code_file_outline for efficient code retrieval instead of reading full files.",
        }

    def get_stats(self) -> dict[str, Any] | None:
        index = self._load_index()
        if not index:
            return None
        return index.get("stats")
