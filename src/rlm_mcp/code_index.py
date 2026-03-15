"""Multi-language code indexer with symbol-level retrieval via tree-sitter.

Indexes a codebase once, then provides O(1) byte-offset retrieval of
individual symbols (functions, classes, methods, types, constants).
Falls back to Python built-in ``ast`` for .py files when tree-sitter
is unavailable.
"""

from __future__ import annotations

import ast as python_ast
from bisect import bisect_right
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
    "html": {
        "extensions": {".html", ".htm", ".djhtml", ".jinja", ".jinja2", ".j2"},
        "grammar": "html",
        "symbol_nodes": {},
    },
}

# Extension → language key lookup
_EXT_TO_LANG: dict[str, str] = {}
for _lang_name, _cfg in LANG_CONFIG.items():
    for _ext in _cfg["extensions"]:
        _EXT_TO_LANG[_ext] = _lang_name


TEMPLATE_TOKEN_RE = re.compile(r"({{.*?}}|{#.*?#}|{%.*?%})", re.DOTALL)
HTML_TAG_RE = re.compile(
    r"<(?P<closing>/)?(?P<tag>[A-Za-z][A-Za-z0-9:_-]*)(?P<attrs>[^<>]*?)(?P<selfclosing>/?)>",
    re.DOTALL,
)
HTML_ATTR_RE = re.compile(
    r"([:@A-Za-z_][\w:.-]*)(?:\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s\"'>/=`]+))?",
)
QUOTED_LITERAL_RE = re.compile(r"['\"]([^'\"]+)['\"]")
VOID_HTML_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}
HTML_SYMBOL_KINDS = {
    "form": "form",
    "section": "section",
    "main": "section",
    "nav": "section",
    "article": "section",
    "aside": "section",
    "header": "section",
    "footer": "section",
    "table": "table",
    "dialog": "section",
    "template": "template",
    "ul": "list",
    "ol": "list",
}
TEMPLATE_BLOCK_TAGS = {
    "block": ("endblock", "block"),
    "if": ("endif", "condition"),
    "for": ("endfor", "loop"),
    "with": ("endwith", "scope"),
    "filter": ("endfilter", "filter"),
    "comment": ("endcomment", "comment"),
    "autoescape": ("endautoescape", "directive"),
    "blocktranslate": ("endblocktranslate", "translation"),
    "spaceless": ("endspaceless", "directive"),
    "verbatim": ("endverbatim", "directive"),
}
TEMPLATE_NON_STRUCTURAL_TAGS = {"else", "elif", "empty", "endifequal", "endifchanged"}


# ================================================================
# Tree-sitter symbol extraction helpers
# ================================================================

def _read_bytes_safe(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        return b""


def _decode_source_bytes(source_bytes: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return source_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return source_bytes.decode("utf-8", errors="replace")


def _compact_text(value: str, limit: int = 120) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def _build_char_to_byte_map(source_text: str) -> list[int]:
    offsets = [0]
    byte_pos = 0
    for ch in source_text:
        byte_pos += len(ch.encode("utf-8"))
        offsets.append(byte_pos)
    return offsets


def _line_start_chars(source_text: str) -> list[int]:
    starts = [0]
    for idx, ch in enumerate(source_text):
        if ch == "\n":
            starts.append(idx + 1)
    return starts


def _char_to_line(line_starts: list[int], char_offset: int) -> int:
    return max(1, bisect_right(line_starts, char_offset))


def _make_symbol_from_chars(
    *,
    file_rel_path: str,
    language: str,
    kind: str,
    name: str,
    qualified_name: str,
    start_char: int,
    end_char: int,
    source_text: str,
    char_to_byte: list[int],
    line_starts: list[int],
    signature: str | None = None,
) -> dict[str, Any]:
    start_byte = char_to_byte[max(0, start_char)]
    end_byte = char_to_byte[max(start_char, end_char)]
    start_line = _char_to_line(line_starts, start_char)
    end_line = _char_to_line(line_starts, max(start_char, end_char - 1))
    symbol_signature = signature or _compact_text(source_text[start_char:end_char], limit=200)
    symbol_id = f"{file_rel_path}::{qualified_name}#{kind}"
    return {
        "symbol_id": symbol_id,
        "name": name,
        "qualified_name": qualified_name,
        "kind": kind,
        "file_path": file_rel_path,
        "language": language,
        "signature": symbol_signature[:200],
        "start_byte": start_byte,
        "end_byte": end_byte,
        "start_line": start_line,
        "end_line": end_line,
        "chars": max(0, end_byte - start_byte),
    }


def _dedupe_symbol_ids(symbols: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, int] = {}
    for sym in symbols:
        symbol_id = sym["symbol_id"]
        count = seen.get(symbol_id, 0)
        if count:
            sym["symbol_id"] = f"{symbol_id}@L{sym['start_line']}"
        seen[symbol_id] = count + 1
    return symbols


def _template_tag_parts(inner: str) -> tuple[str, str]:
    compact = inner.strip()
    if not compact:
        return "", ""
    parts = compact.split(None, 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def _extract_quoted_literal(text: str) -> str | None:
    match = QUOTED_LITERAL_RE.search(text)
    if not match:
        return None
    return match.group(1).strip() or None


def _template_variable_parts(expression: str) -> tuple[str, str]:
    qualified = _compact_text(expression, limit=120)
    base = expression.split("|", 1)[0].split(":", 1)[0].strip()
    root = re.split(r"[.\[(\s]", base, maxsplit=1)[0].strip()
    return (root or qualified or "variable"), qualified or root or "variable"


def _paired_template_symbol(tag_name: str, body: str) -> tuple[str, str, str, str] | None:
    entry = TEMPLATE_BLOCK_TAGS.get(tag_name)
    if entry is None:
        return None

    end_tag, kind = entry
    body_compact = _compact_text(body)

    if tag_name == "block":
        name = body.split()[0] if body.split() else "block"
        qualified_name = f"block.{name}"
    elif tag_name == "for":
        name = body.split(" in ", 1)[0].replace("for ", "").strip() or "for"
        qualified_name = body_compact or name
    elif tag_name == "if":
        name = body_compact.split()[0] if body_compact else "if"
        qualified_name = body_compact or name
    else:
        name = body_compact or tag_name
        qualified_name = f"{tag_name}.{name}" if name != tag_name else tag_name

    return kind, name, qualified_name, end_tag


def _single_template_symbol(tag_name: str, body: str) -> tuple[str, str, str] | None:
    if tag_name in TEMPLATE_NON_STRUCTURAL_TAGS or tag_name.startswith("end"):
        return None

    quoted = _extract_quoted_literal(body)
    body_compact = _compact_text(body)

    if tag_name == "extends":
        name = quoted or body_compact or "extends"
        return "extends", name, name
    if tag_name == "include":
        name = quoted or body_compact or "include"
        return "include", name, name
    if tag_name == "load":
        name = body_compact or "load"
        return "load", name, name
    if tag_name == "url":
        name = quoted or body_compact or "url"
        return "url", name, name
    if tag_name == "csrf_token":
        return "tag", "csrf_token", "csrf_token"

    name = body_compact or tag_name
    qualified_name = f"{tag_name}.{name}" if name != tag_name else tag_name
    return "tag", name, qualified_name


def _parse_html_attrs(attrs_text: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in HTML_ATTR_RE.finditer(attrs_text):
        key = match.group(1).lower()
        raw_value = (match.group(2) or "").strip()
        if raw_value[:1] in {'"', "'"} and raw_value[-1:] == raw_value[:1]:
            raw_value = raw_value[1:-1]
        attrs[key] = raw_value
    return attrs


def _html_symbol_identity(tag: str, attrs: dict[str, str]) -> tuple[str, str, str] | None:
    kind = HTML_SYMBOL_KINDS.get(tag)
    if kind is None and tag in {"div", "span"} and not any(
        key in attrs for key in ("id", "data-component", "data-testid", "role")
    ):
        return None
    if kind is None and "id" not in attrs:
        return None

    name = (
        attrs.get("id")
        or attrs.get("name")
        or attrs.get("data-component")
        or attrs.get("data-testid")
        or attrs.get("aria-label")
        or attrs.get("role")
    )
    if not name and attrs.get("class"):
        name = attrs["class"].split()[0]
    if not name:
        name = tag

    effective_kind = kind or "element"
    qualified_name = f"{tag}.{name}" if name != tag else tag
    return effective_kind, name, qualified_name


def _html_template_extract(source_bytes: bytes, file_rel_path: str) -> list[dict[str, Any]]:
    source_text = _decode_source_bytes(source_bytes)
    char_to_byte = _build_char_to_byte_map(source_text)
    line_starts = _line_start_chars(source_text)
    symbols: list[dict[str, Any]] = []

    template_stack: list[dict[str, Any]] = []
    for match in TEMPLATE_TOKEN_RE.finditer(source_text):
        token = match.group(0)
        start_char, end_char = match.span()

        if token.startswith("{#"):
            continue

        if token.startswith("{{"):
            name, qualified_name = _template_variable_parts(token[2:-2].strip())
            symbols.append(
                _make_symbol_from_chars(
                    file_rel_path=file_rel_path,
                    language="html",
                    kind="variable",
                    name=name,
                    qualified_name=qualified_name,
                    start_char=start_char,
                    end_char=end_char,
                    source_text=source_text,
                    char_to_byte=char_to_byte,
                    line_starts=line_starts,
                    signature=_compact_text(token, limit=200),
                )
            )
            continue

        inner = token[2:-2].strip()
        tag_name, body = _template_tag_parts(inner)
        if not tag_name:
            continue

        if tag_name.startswith("end"):
            for idx in range(len(template_stack) - 1, -1, -1):
                open_item = template_stack[idx]
                if open_item["end_tag"] == tag_name:
                    template_stack.pop(idx)
                    symbols.append(
                        _make_symbol_from_chars(
                            file_rel_path=file_rel_path,
                            language="html",
                            kind=open_item["kind"],
                            name=open_item["name"],
                            qualified_name=open_item["qualified_name"],
                            start_char=open_item["start_char"],
                            end_char=end_char,
                            source_text=source_text,
                            char_to_byte=char_to_byte,
                            line_starts=line_starts,
                            signature=open_item["signature"],
                        )
                    )
                    break
            continue

        paired = _paired_template_symbol(tag_name, body)
        if paired is not None:
            kind, name, qualified_name, end_tag = paired
            template_stack.append(
                {
                    "kind": kind,
                    "name": name,
                    "qualified_name": qualified_name,
                    "end_tag": end_tag,
                    "start_char": start_char,
                    "fallback_end_char": end_char,
                    "signature": _compact_text(token, limit=200),
                }
            )
            continue

        single = _single_template_symbol(tag_name, body)
        if single is None:
            continue
        kind, name, qualified_name = single
        symbols.append(
            _make_symbol_from_chars(
                file_rel_path=file_rel_path,
                language="html",
                kind=kind,
                name=name,
                qualified_name=qualified_name,
                start_char=start_char,
                end_char=end_char,
                source_text=source_text,
                char_to_byte=char_to_byte,
                line_starts=line_starts,
                signature=_compact_text(token, limit=200),
            )
        )

    for open_item in template_stack:
        symbols.append(
            _make_symbol_from_chars(
                file_rel_path=file_rel_path,
                language="html",
                kind=open_item["kind"],
                name=open_item["name"],
                qualified_name=open_item["qualified_name"],
                start_char=open_item["start_char"],
                end_char=open_item["fallback_end_char"],
                source_text=source_text,
                char_to_byte=char_to_byte,
                line_starts=line_starts,
                signature=open_item["signature"],
            )
        )

    html_stack: list[dict[str, Any]] = []
    for match in HTML_TAG_RE.finditer(source_text):
        tag = match.group("tag").lower()
        start_char, end_char = match.span()
        is_closing = bool(match.group("closing"))
        is_self_closing = bool(match.group("selfclosing")) or tag in VOID_HTML_TAGS

        if is_closing:
            for idx in range(len(html_stack) - 1, -1, -1):
                open_item = html_stack[idx]
                if open_item["tag"] == tag:
                    html_stack.pop(idx)
                    symbols.append(
                        _make_symbol_from_chars(
                            file_rel_path=file_rel_path,
                            language="html",
                            kind=open_item["kind"],
                            name=open_item["name"],
                            qualified_name=open_item["qualified_name"],
                            start_char=open_item["start_char"],
                            end_char=end_char,
                            source_text=source_text,
                            char_to_byte=char_to_byte,
                            line_starts=line_starts,
                            signature=open_item["signature"],
                        )
                    )
                    break
            continue

        attrs = _parse_html_attrs(match.group("attrs") or "")
        identity = _html_symbol_identity(tag, attrs)
        if identity is None:
            continue

        kind, name, qualified_name = identity
        signature = _compact_text(match.group(0), limit=200)
        if is_self_closing:
            symbols.append(
                _make_symbol_from_chars(
                    file_rel_path=file_rel_path,
                    language="html",
                    kind=kind,
                    name=name,
                    qualified_name=qualified_name,
                    start_char=start_char,
                    end_char=end_char,
                    source_text=source_text,
                    char_to_byte=char_to_byte,
                    line_starts=line_starts,
                    signature=signature,
                )
            )
            continue

        html_stack.append(
            {
                "tag": tag,
                "kind": kind,
                "name": name,
                "qualified_name": qualified_name,
                "start_char": start_char,
                "fallback_end_char": end_char,
                "signature": signature,
            }
        )

    for open_item in html_stack:
        symbols.append(
            _make_symbol_from_chars(
                file_rel_path=file_rel_path,
                language="html",
                kind=open_item["kind"],
                name=open_item["name"],
                qualified_name=open_item["qualified_name"],
                start_char=open_item["start_char"],
                end_char=open_item["fallback_end_char"],
                source_text=source_text,
                char_to_byte=char_to_byte,
                line_starts=line_starts,
                signature=open_item["signature"],
            )
        )

    symbols.sort(key=lambda item: (item["start_byte"], item["end_byte"], item["name"]))
    return _dedupe_symbol_ids(symbols)


def _extract_name(node: Any, source_bytes: bytes, language: str) -> str:
    """Extract symbol name from a tree-sitter AST node."""
    # CSS: selector text or at-rule preamble
    if language in ("css", "scss"):
        if node.type == "rule_set":
            for child in node.children:
                if "selector" in child.type.lower():
                    txt = _decode_source_bytes(
                        source_bytes[child.start_byte:child.end_byte]
                    )
                    return txt.strip()[:80]
        txt = _decode_source_bytes(
            source_bytes[node.start_byte : min(node.start_byte + 80, node.end_byte)]
        )
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
            return _decode_source_bytes(
                source_bytes[child.start_byte : child.end_byte]
            )

    # Fallback: first line text
    txt = _decode_source_bytes(
        source_bytes[node.start_byte : min(node.start_byte + 80, node.end_byte)]
    )
    first_line = txt.split("\n")[0].strip()
    return first_line[:60] or f"<{node.type}>"


def _extract_signature(source_bytes: bytes, start_byte: int, end_byte: int) -> str:
    """Extract compact human-readable signature from byte range."""
    chunk = _decode_source_bytes(
        source_bytes[start_byte : min(start_byte + 500, end_byte)]
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

        if language == "html":
            try:
                return _html_template_extract(source_bytes, file_rel_path)
            except Exception:
                return []

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
                return _dedupe_symbol_ids(symbols)
            except Exception:
                pass  # fall through

        # Python fallback via built-in ast
        if language == "python":
            try:
                source_text = _decode_source_bytes(source_bytes)
                return _dedupe_symbol_ids(_python_ast_extract(source_text, file_rel_path))
            except Exception:
                return []

        return []

    def _extract_symbols_for_path(self, file_path: str) -> list[dict[str, Any]]:
        abs_path = self.resolve_file_path(file_path)
        try:
            rel_path = abs_path.relative_to(self.project_root).as_posix()
        except ValueError:
            return []

        language = _EXT_TO_LANG.get(abs_path.suffix.lower())
        if language is None:
            return []

        source_bytes = _read_bytes_safe(abs_path)
        if not source_bytes:
            return []

        return self._extract_symbols(source_bytes, rel_path, language)

    def _score_symbol_match(
        self,
        sym: dict[str, Any],
        query_lower: str,
        *,
        kind: str | None = None,
        language: str | None = None,
    ) -> int:
        if kind and sym["kind"] != kind:
            return 0
        if language and sym["language"] != language:
            return 0

        name_lower = sym["name"].lower()
        qn_lower = sym["qualified_name"].lower()
        signature_lower = sym.get("signature", "").lower()
        file_path_lower = sym.get("file_path", "").lower()

        if name_lower == query_lower:
            return 100
        if qn_lower == query_lower:
            return 95
        if query_lower in name_lower:
            return 80
        if query_lower in qn_lower:
            return 70
        if query_lower in signature_lower:
            return 50
        if query_lower in file_path_lower:
            return 40
        return 0

    def _iter_project_file_paths(
        self,
        *,
        language: str | None = None,
        exclude_paths: set[str] | None = None,
    ) -> Iterable[str]:
        excluded = exclude_paths or set()
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            dirs[:] = [
                d for d in dirs
                if d not in IGNORE_DIRS and not (d.startswith(".") and d != ".github")
            ]

            for fname in sorted(files):
                file_path = root_path / fname
                suffix = file_path.suffix.lower()
                file_language = _EXT_TO_LANG.get(suffix)
                if file_language is None:
                    continue
                if language and file_language != language:
                    continue

                rel_path = file_path.relative_to(self.project_root).as_posix()
                if rel_path in excluded or rel_path.startswith(("memory/", ".git/")):
                    continue
                yield rel_path

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
        query_lower = query.lower()
        results: list[dict[str, Any]] = []

        def _collect(symbols: Iterable[dict[str, Any]]) -> None:
            for sym in symbols:
                score = self._score_symbol_match(
                    sym,
                    query_lower,
                    kind=kind,
                    language=language,
                )
                if score > 0:
                    results.append({**sym, "_score": score})

        indexed_symbols = index.get("symbols", []) if index else []
        _collect(indexed_symbols)

        should_scan_template_fallback = language in (None, "html") and len(results) < max_results
        if should_scan_template_fallback:
            indexed_paths = {
                sym["file_path"]
                for sym in indexed_symbols
                if sym.get("language") == "html"
            }
            scanned_files = 0
            for rel_path in self._iter_project_file_paths(
                language="html",
                exclude_paths=indexed_paths,
            ):
                _collect(self._extract_symbols_for_path(rel_path))
                scanned_files += 1
                if scanned_files >= 300 and len(results) >= max_results:
                    break

        deduped: dict[str, dict[str, Any]] = {}
        for item in results:
            symbol_id = item["symbol_id"]
            existing = deduped.get(symbol_id)
            if existing is None or item["_score"] > existing["_score"]:
                deduped[symbol_id] = item

        ordered = sorted(
            deduped.values(),
            key=lambda x: (-x["_score"], x["name"], x.get("file_path", "")),
        )
        for r in ordered[:max_results]:
            r.pop("_score", None)
        return ordered[:max_results]

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

                source = _decode_source_bytes(
                    source_bytes[sym["start_byte"] : sym["end_byte"]]
                )
                return {
                    **sym,
                    "source": source,
                    "source_chars": len(source),
                    "source_tokens_est": max(1, len(source) // 4),
                }
        return None

    def normalize_file_path(self, file_path: str) -> str:
        path = Path(file_path)
        if path.is_absolute():
            try:
                return path.resolve().relative_to(self.project_root).as_posix()
            except ValueError:
                return path.resolve().as_posix()
        return path.as_posix()

    def resolve_file_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if path.is_absolute():
            return path.resolve()
        return (self.project_root / path).resolve()

    # ---------- file outline ----------

    def get_file_outline(self, file_path: str) -> list[dict[str, Any]]:
        """Return symbol outline for a specific file (no source bodies)."""
        index = self._load_index()
        normalized_path = self.normalize_file_path(file_path)

        compact_keys = (
            "symbol_id", "name", "qualified_name", "kind", "language",
            "signature", "start_line", "end_line", "chars",
        )
        if index:
            outline = [
                {k: sym[k] for k in compact_keys if k in sym}
                for sym in index["symbols"]
                if sym["file_path"] == normalized_path
            ]
            if outline:
                return outline

        return [
            {k: sym[k] for k in compact_keys if k in sym}
            for sym in self._extract_symbols_for_path(normalized_path)
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
