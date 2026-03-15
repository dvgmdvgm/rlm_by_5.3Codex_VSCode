from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


ALLOWED_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".yml",
    ".yaml",
    ".md",
    ".css",
    ".scss",
    ".sass",
    ".html",
    ".htm",
    ".djhtml",
    ".jinja",
    ".jinja2",
    ".j2",
    ".vue",
    ".kt",
    ".java",
    ".swift",
    ".dart",
    ".go",
    ".rs",
    ".sql",
    ".sh",
    ".ps1",
}

IGNORE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    ".vs",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "out",
    "target",
    "bin",
    "obj",
    "Pods",
    "DerivedData",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".dart_tool",
    ".gradle",
}

CATEGORY_DIRS = {
    "01_project": ["project_summary.md"],
    "02_architecture": ["system_overview.md", "module_map.md"],
    "03_decisions": ["inferred_decisions.md"],
    "04_domain": ["domain_entities.md"],
    "05_code": ["code_inventory.md", "integration_points.md"],
    "06_problems": ["hotspots.md"],
    "07_context": ["implementation_patterns.md"],
    "08_people": ["collaboration_notes.md"],
    "09_external": ["dependencies.md"],
    "10_testing": ["test_strategy.md"],
    "11_deployment": ["runtime_environment.md"],
    "12_roadmap": ["next_steps_bootstrap.md"],
    "13_preferences": ["coding_style_inferred.md"],
}

FRAMEWORK_HINTS = {
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "react-native": "React Native",
    "expo": "Expo",
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "express": "Express",
    "nestjs": "NestJS",
    "spring-boot": "Spring Boot",
    "kotlin": "Kotlin",
    "flutter": "Flutter",
    "swiftui": "SwiftUI",
    "typeorm": "TypeORM",
    "prisma": "Prisma",
    "sqlalchemy": "SQLAlchemy",
    "tailwindcss": "TailwindCSS",
    "styled-components": "styled-components",
    "redux": "Redux",
    "zustand": "Zustand",
    "mobx": "MobX",
    "celery": "Celery",
    "redis": "Redis",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
}

ROUTE_PATTERNS = [
    re.compile(r"@(?:app|router)\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]+)"),
    re.compile(r"\bpath\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"\bre_path\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"<Route\s+[^>]*path=['\"]([^'\"]+)['\"]"),
    re.compile(r"router\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]+)['\"]"),
]

IMPORT_PATTERNS = {
    ".py": [re.compile(r"^\s*from\s+([\w\.]+)\s+import\s+", re.MULTILINE), re.compile(r"^\s*import\s+([\w\.]+)", re.MULTILINE)],
    ".js": [re.compile(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]"), re.compile(r"require\(['\"]([^'\"]+)['\"]\)")],
    ".jsx": [re.compile(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]"), re.compile(r"require\(['\"]([^'\"]+)['\"]\)")],
    ".ts": [re.compile(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]"), re.compile(r"require\(['\"]([^'\"]+)['\"]\)")],
    ".tsx": [re.compile(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]"), re.compile(r"require\(['\"]([^'\"]+)['\"]\)")],
}

ENTITY_PATTERNS = [
    re.compile(r"class\s+([A-Z][A-Za-z0-9_]{2,})"),
    re.compile(r"interface\s+([A-Z][A-Za-z0-9_]{2,})"),
    re.compile(r"type\s+([A-Z][A-Za-z0-9_]{2,})\s*="),
    re.compile(r"model\s+([A-Z][A-Za-z0-9_]{2,})", re.IGNORECASE),
]

COLOR_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
TAILWIND_COLOR_RE = re.compile(r"\b(?:bg|text|border)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b")
ANIMATION_RE = re.compile(r"\b(animation|transition|framer-motion|react-spring|lottie|gsap)\b", re.IGNORECASE)
REASON_RE = re.compile(r"\b(because|so that|in order to|чтобы|потому что|для того чтобы)\b", re.IGNORECASE)
TEST_NAME_RE = re.compile(r"(test|spec)\.(py|js|jsx|ts|tsx)$", re.IGNORECASE)
SCREEN_FILE_RE = re.compile(r"Screen\.(jsx|tsx|js|ts)$", re.IGNORECASE)


@dataclass
class SourceFile:
    path: Path
    rel_path: str
    suffix: str
    chars: int
    lines: int
    text: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text_safe(path: Path) -> str:
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


def iter_source_files(project_root: Path, include_hidden: bool, max_file_chars: int) -> Iterable[SourceFile]:
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)

        filtered_dirs: list[str] = []
        for d in dirs:
            if d in IGNORE_DIRS:
                continue
            if not include_hidden and d.startswith(".") and d not in {".github"}:
                continue
            filtered_dirs.append(d)
        dirs[:] = filtered_dirs

        for name in files:
            file_path = root_path / name
            rel = file_path.relative_to(project_root).as_posix()
            suffix = file_path.suffix.lower()
            if suffix not in ALLOWED_SUFFIXES:
                continue
            text = read_text_safe(file_path)
            if not text:
                continue
            if len(text) > max_file_chars:
                text = text[:max_file_chars]
            yield SourceFile(
                path=file_path,
                rel_path=rel,
                suffix=suffix,
                chars=len(text),
                lines=text.count("\n") + 1,
                text=text,
            )


def parse_package_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def parse_requirements(path: Path) -> list[str]:
    if not path.exists():
        return []
    result: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        result.append(line)
    return result


def parse_pyproject(path: Path) -> dict:
    if not path.exists() or tomllib is None:
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def detect_frameworks(dep_names: Iterable[str], source_files: list[SourceFile]) -> list[str]:
    found = set()
    lowered = {d.lower() for d in dep_names}
    for dep in lowered:
        for key, label in FRAMEWORK_HINTS.items():
            if key in dep:
                found.add(label)

    root_paths = {sf.rel_path.lower() for sf in source_files[:5000]}
    if any("android/" in p for p in root_paths):
        found.add("Android")
    if any("ios/" in p for p in root_paths):
        found.add("iOS")
    if any("app.json" in p for p in root_paths):
        found.add("JavaScript App")

    return sorted(found)


def _extract_import_values(sf: SourceFile) -> list[str]:
    values: list[str] = []
    patterns = IMPORT_PATTERNS.get(sf.suffix, [])
    for pattern in patterns:
        for match in pattern.findall(sf.text):
            value = match if isinstance(match, str) else (match[0] if match else "")
            if value:
                values.append(value)
    return values


def extract_imports(source_files: list[SourceFile]) -> Counter:
    counter: Counter[str] = Counter()
    for sf in source_files:
        for value in _extract_import_values(sf):
            counter[value] += 1
    return counter


def extract_import_edges(source_files: list[SourceFile]) -> Counter[tuple[str, str]]:
    edges: Counter[tuple[str, str]] = Counter()
    for sf in source_files:
        for value in _extract_import_values(sf):
            edges[(sf.rel_path, value)] += 1
    return edges


def _python_module_map(source_files: list[SourceFile]) -> dict[str, str]:
    mod_map: dict[str, str] = {}
    for sf in source_files:
        if sf.suffix != ".py":
            continue
        rel_no_ext = sf.rel_path[:-3]
        dotted = rel_no_ext.replace("/", ".")
        if dotted.endswith(".__init__"):
            dotted = dotted[: -len(".__init__")]
        mod_map[dotted] = sf.rel_path
        if dotted.startswith("src."):
            mod_map[dotted[4:]] = sf.rel_path
    return mod_map


def _resolve_js_relative_import(src_rel: str, import_value: str, source_path_set: set[str]) -> str | None:
    src_dir = Path(src_rel).parent
    base = (src_dir / import_value).as_posix()
    candidates = [base]
    if Path(base).suffix == "":
        for ext in (".js", ".jsx", ".ts", ".tsx", ".vue"):
            candidates.append(base + ext)
            candidates.append((Path(base) / ("index" + ext)).as_posix())
    for cand in candidates:
        if cand in source_path_set:
            return cand
    return None


def build_json_graph(project_root: Path, source_files: list[SourceFile], import_edges: Counter[tuple[str, str]]) -> dict:
    source_path_set = {sf.rel_path for sf in source_files}
    py_mod_map = _python_module_map(source_files)

    nodes: dict[str, dict] = {}
    for sf in source_files:
        nodes[sf.rel_path] = {
            "id": sf.rel_path,
            "type": "source",
            "path": sf.rel_path,
            "suffix": sf.suffix,
            "chars": sf.chars,
            "lines": sf.lines,
            "top_dir": sf.rel_path.split("/")[0],
        }

    edge_rows: list[dict] = []
    for (src, raw_import), count in import_edges.items():
        resolved_target: str | None = None
        src_suffix = Path(src).suffix.lower()

        if src_suffix == ".py":
            resolved_target = py_mod_map.get(raw_import)
            if resolved_target is None:
                for candidate_mod in py_mod_map:
                    if candidate_mod.startswith(raw_import + "."):
                        resolved_target = py_mod_map[candidate_mod]
                        break
        elif src_suffix in {".js", ".jsx", ".ts", ".tsx", ".vue"} and raw_import.startswith("."):
            resolved_target = _resolve_js_relative_import(src, raw_import, source_path_set)

        if resolved_target is None:
            target_id = f"pkg:{raw_import}"
            if target_id not in nodes:
                nodes[target_id] = {
                    "id": target_id,
                    "type": "external",
                    "module": raw_import,
                }
            is_internal = False
        else:
            target_id = resolved_target
            is_internal = True

        edge_rows.append(
            {
                "source": src,
                "target": target_id,
                "kind": "import",
                "raw_import": raw_import,
                "count": count,
                "is_internal": is_internal,
            }
        )

    source_nodes = sum(1 for n in nodes.values() if n.get("type") == "source")
    external_nodes = sum(1 for n in nodes.values() if n.get("type") == "external")

    return {
        "generated_at": utc_now(),
        "project_root": project_root.as_posix(),
        "stats": {
            "nodes_total": len(nodes),
            "source_nodes": source_nodes,
            "external_nodes": external_nodes,
            "edges_total": len(edge_rows),
            "internal_edges": sum(1 for e in edge_rows if e["is_internal"]),
            "external_edges": sum(1 for e in edge_rows if not e["is_internal"]),
        },
        "nodes": list(nodes.values()),
        "edges": edge_rows,
    }


def extract_routes(source_files: list[SourceFile]) -> Counter:
    routes: Counter[str] = Counter()
    for sf in source_files:
        for pattern in ROUTE_PATTERNS:
            matches = pattern.findall(sf.text)
            for match in matches:
                if isinstance(match, tuple):
                    candidate = match[-1]
                else:
                    candidate = match
                if candidate:
                    routes[candidate] += 1
    return routes


def extract_entities(source_files: list[SourceFile]) -> Counter:
    entities: Counter[str] = Counter()
    for sf in source_files:
        for pattern in ENTITY_PATTERNS:
            for name in pattern.findall(sf.text):
                entities[name] += 1
    return entities


def infer_decisions(source_files: list[SourceFile], frameworks: list[str], routes: Counter) -> list[str]:
    decisions: list[str] = []
    rel_paths = [sf.rel_path.lower() for sf in source_files]

    if any("dockerfile" in p for p in rel_paths):
        decisions.append("Deployment likely containerized (Dockerfile detected). [confidence: high]")
    if any(".github/workflows/" in p for p in rel_paths):
        decisions.append("CI/CD automation is present via GitHub Actions workflows. [confidence: high]")
    if "React Native" in frameworks and "Expo" in frameworks:
        decisions.append("Mobile stack likely chosen for fast cross-platform delivery (React Native + Expo). [confidence: medium]")
    if "Django" in frameworks and routes:
        decisions.append("Backend likely organized around explicit URL routing and server-side API boundaries. [confidence: medium]")
    if any("prisma" in p for p in rel_paths):
        decisions.append("Schema-first data modeling is likely used (Prisma artifacts found). [confidence: medium]")

    reason_hits = 0
    for sf in source_files[:2000]:
        reason_hits += len(REASON_RE.findall(sf.text))
    if reason_hits > 20:
        decisions.append("Codebase contains explicit rationale comments/documentation in multiple places. [confidence: medium]")
    elif reason_hits == 0:
        decisions.append("Architectural rationale is mostly implicit in code; consider documenting explicit ADR-style decisions. [confidence: high]")

    if not decisions:
        decisions.append("No strong explicit architecture decisions inferred; requires targeted manual review of core modules. [confidence: low]")

    return decisions


def build_analysis(project_root: Path, source_files: list[SourceFile]) -> dict:
    ext_counts = Counter(sf.suffix for sf in source_files)
    top_files = sorted(source_files, key=lambda sf: sf.chars, reverse=True)[:30]

    package_json = parse_package_json(project_root / "package.json")
    pyproject = parse_pyproject(project_root / "pyproject.toml")
    requirements = parse_requirements(project_root / "requirements.txt")
    requirements_dev = parse_requirements(project_root / "requirements-dev.txt")

    dependencies = set()
    if package_json:
        dependencies.update((package_json.get("dependencies") or {}).keys())
        dependencies.update((package_json.get("devDependencies") or {}).keys())
    if pyproject:
        dependencies.update(pyproject.get("project", {}).get("dependencies", []))
    dependencies.update(requirements)
    dependencies.update(requirements_dev)

    frameworks = detect_frameworks(dependencies, source_files)
    imports = extract_imports(source_files)
    import_edges = extract_import_edges(source_files)
    routes = extract_routes(source_files)
    entities = extract_entities(source_files)
    decisions = infer_decisions(source_files, frameworks, routes)

    screen_files = [sf.rel_path for sf in source_files if SCREEN_FILE_RE.search(sf.rel_path)]
    test_files = [sf.rel_path for sf in source_files if TEST_NAME_RE.search(sf.rel_path)]

    hex_colors = Counter()
    tw_colors = Counter()
    animations = Counter()
    reason_lines: list[str] = []

    for sf in source_files:
        for color in COLOR_HEX_RE.findall(sf.text):
            hex_colors[color.lower()] += 1
        for cls in TAILWIND_COLOR_RE.findall(sf.text):
            tw_colors[cls] += 1
        for anim in ANIMATION_RE.findall(sf.text):
            animations[anim.lower()] += 1

        if len(reason_lines) < 30:
            for i, line in enumerate(sf.text.splitlines(), start=1):
                if REASON_RE.search(line):
                    reason_lines.append(f"{sf.rel_path}#L{i}: {line.strip()[:220]}")
                if len(reason_lines) >= 30:
                    break

    directory_counts: Counter[str] = Counter()
    for sf in source_files:
        top = sf.rel_path.split("/")[0]
        directory_counts[top] += 1

    return {
        "generated_at": utc_now(),
        "project_root": project_root.as_posix(),
        "file_count": len(source_files),
        "total_chars_scanned": sum(sf.chars for sf in source_files),
        "total_lines_scanned": sum(sf.lines for sf in source_files),
        "extensions": ext_counts,
        "top_files": top_files,
        "frameworks": frameworks,
        "dependencies": sorted(str(d) for d in dependencies),
        "imports": imports,
        "import_edges": import_edges,
        "routes": routes,
        "entities": entities,
        "decisions": decisions,
        "screen_files": screen_files,
        "test_files": test_files,
        "hex_colors": hex_colors,
        "tailwind_colors": tw_colors,
        "animations": animations,
        "reason_lines": reason_lines,
        "directory_counts": directory_counts,
    }


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def md_list(items: Iterable[str], limit: int = 20) -> str:
    out = []
    for idx, item in enumerate(items):
        if idx >= limit:
            break
        out.append(f"- {item}")
    return "\n".join(out) if out else "- (none)"


def md_counter(counter: Counter, limit: int = 20) -> str:
    return md_list((f"`{k}` — {v}" for k, v in counter.most_common(limit)), limit=limit)


def render_index(category: str, files: list[str], generated_at: str) -> str:
    file_rows = "\n".join(f"| `{name}` | Generated | {generated_at[:10]} |" for name in files)
    return f"""# 📁 {category.upper()}\n\n> Auto-generated from codebase scan\n> Generated: {generated_at}\n\n## Files\n\n| File | Description | Updated |\n|------|-------------|---------|\n{file_rows}\n"""


def render_project_summary(a: dict) -> str:
    return f"""# Project Summary (Code-Derived)\n\n## Scan Meta\n- Generated at: `{a['generated_at']}`\n- Project root: `{a['project_root']}`\n- Source files scanned: **{a['file_count']}**\n- Total scanned chars: **{a['total_chars_scanned']}**\n- Total scanned lines: **{a['total_lines_scanned']}**\n\n## Top-level Structure\n{md_counter(a['directory_counts'], 25)}\n\n## Language/Extension Mix\n{md_counter(a['extensions'], 20)}\n\n## Framework Signals\n{md_list(a['frameworks'], 30)}\n"""


def render_system_overview(a: dict) -> str:
    return f"""# System Overview\n\n## Architecture Signals\n- Detected frameworks/stacks:\n{md_list(a['frameworks'], 30)}\n\n## Route/API Surface (inferred)\n{md_counter(a['routes'], 40)}\n\n## Domain Entities (inferred class/type/model names)\n{md_counter(a['entities'], 40)}\n\n## Notes\n- Items in this document are inferred from source code patterns, not from memory files.\n- Use as bootstrap context, then refine manually for high-critical decisions.\n"""


def render_module_map(a: dict) -> str:
    top_imports = md_counter(a['imports'], 60)
    top_files = "\n".join(
        f"- `{sf.rel_path}` — {sf.chars} chars, {sf.lines} lines" for sf in a['top_files'][:25]
    )
    if not top_files:
        top_files = "- (none)"
    return f"""# Module Map\n\n## Most Referenced Imports\n{top_imports}\n\n## Largest Files (potential core modules)\n{top_files}\n"""


def render_decisions(a: dict) -> str:
    return f"""# Inferred Decisions\n\n## Decision Hypotheses\n{md_list(a['decisions'], 30)}\n\n## Evidence snippets (why-pattern comments)\n{md_list(a['reason_lines'], 30)}\n\n## Confidence policy\n- high: direct file/config evidence\n- medium: strong implementation pattern\n- low: weak signal, requires manual confirmation\n"""


def render_domain(a: dict) -> str:
    return f"""# Domain Entities\n\n## Detected Entity Candidates\n{md_counter(a['entities'], 80)}\n\n## Mobile Screen Candidates\n{md_list(a['screen_files'], 80)}\n"""


def render_code_inventory(a: dict) -> str:
    top_files = "\n".join(
        f"- `{sf.rel_path}` — {sf.chars} chars" for sf in a['top_files'][:40]
    )
    if not top_files:
        top_files = "- (none)"
    return f"""# Code Inventory\n\n## Largest/Most Complex Files\n{top_files}\n\n## Test Files\n{md_list(a['test_files'], 120)}\n"""


def render_integrations(a: dict) -> str:
    deps = md_list(a['dependencies'], 200)
    return f"""# Integration Points\n\n## Dependency Inventory\n{deps}\n\n## Imported Modules (top)\n{md_counter(a['imports'], 80)}\n\n## API/Route Touchpoints\n{md_counter(a['routes'], 80)}\n"""


def render_hotspots(a: dict) -> str:
    todo_hits: list[str] = []
    for sf in a['top_files']:
        text = sf.text
        if "TODO" in text or "FIXME" in text or "HACK" in text:
            todo_hits.append(sf.rel_path)
    return f"""# Hotspots\n\n## Potential risk files (by size)\n{md_list((f"{sf.rel_path} ({sf.chars} chars)" for sf in a['top_files'][:30]), 30)}\n\n## TODO/FIXME/HACK signals\n{md_list(todo_hits, 80)}\n\n## Suggested first-review set\n- Top 10 largest files\n- Files with TODO/FIXME/HACK markers\n- Core route/config/bootstrap files\n"""


def render_patterns(a: dict) -> str:
    return f"""# Implementation Patterns\n\n## Styling signals\n### HEX colors\n{md_counter(a['hex_colors'], 40)}\n\n### Tailwind color classes\n{md_counter(a['tailwind_colors'], 40)}\n\n### Animation signals\n{md_counter(a['animations'], 40)}\n\n## Reasoning traces in code/comments\n{md_list(a['reason_lines'], 40)}\n"""


def render_people() -> str:
    return """# Collaboration Notes\n\nThis file is intentionally bootstrap-only.\n\nPopulate manually with:\n- team ownership map\n- coding conventions by team\n- decision authority map\n- review/approval routing\n"""


def render_dependencies(a: dict) -> str:
    return f"""# External Dependencies\n\n## Declared dependencies\n{md_list(a['dependencies'], 400)}\n\n## Detected frameworks\n{md_list(a['frameworks'], 40)}\n"""


def render_testing(a: dict) -> str:
    return f"""# Test Strategy (Inferred)\n\n## Detected test files\n{md_list(a['test_files'], 200)}\n\n## Coverage heuristic\n- Test files count: **{len(a['test_files'])}**\n- Total source files: **{a['file_count']}**\n\n## Recommendations\n- Ensure each critical route/module has test coverage.\n- Add integration tests for cross-layer boundaries (API <-> UI/mobile).\n"""


def render_runtime(a: dict) -> str:
    env_hits = [dep for dep in a['dependencies'] if "dotenv" in dep.lower() or "env" in dep.lower()]
    return f"""# Runtime and Deployment (Inferred)\n\n## Runtime signals\n- Frameworks: {', '.join(a['frameworks']) if a['frameworks'] else '(none)'}\n- Environment-related dependencies:\n{md_list(env_hits, 30)}\n\n## Deployment hints\n- Check for Docker/K8s/GitHub Actions artifacts in root for concrete deployment path.\n- This report is code-derived and should be validated against infra configs.\n"""


def render_roadmap(a: dict) -> str:
    return f"""# Bootstrap Roadmap (Generated)\n\n## Phase 1 — Validate inferred architecture\n- Confirm top routes/modules from `02_architecture/*`.\n- Confirm inferred decisions from `03_decisions/inferred_decisions.md`.\n\n## Phase 2 — Stabilize coding rules\n- Convert recurring patterns in `07_context/implementation_patterns.md` into explicit coding rules.\n\n## Phase 3 — Operationalize memory\n- Keep this generated structure in sync with code changes via periodic re-run of the generator.\n\n## Suggested next command\n- Re-run generator after major refactors/releases to keep memory current.\n"""


def render_style(a: dict) -> str:
    return f"""# Coding Style (Inferred from Code)\n\n## Style hints\n- Dominant extensions:\n{md_counter(a['extensions'], 12)}\n\n- Frequent color/style tokens:\n{md_counter(a['tailwind_colors'], 25)}\n\n- Frequent hex palette entries:\n{md_counter(a['hex_colors'], 25)}\n\n## Important note\n- This file stores inferred conventions from existing code.\n- Treat as baseline; convert confirmed conventions into explicit project rules.\n"""


def write_memory_structure(output_dir: Path, analysis: dict) -> None:
    generated_at = analysis["generated_at"]

    for category, files in CATEGORY_DIRS.items():
        category_dir = output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        write_file(category_dir / "_index.md", render_index(category, files, generated_at))

    writers = {
        "01_project/project_summary.md": render_project_summary,
        "02_architecture/system_overview.md": render_system_overview,
        "02_architecture/module_map.md": render_module_map,
        "03_decisions/inferred_decisions.md": render_decisions,
        "04_domain/domain_entities.md": render_domain,
        "05_code/code_inventory.md": render_code_inventory,
        "05_code/integration_points.md": render_integrations,
        "06_problems/hotspots.md": render_hotspots,
        "07_context/implementation_patterns.md": render_patterns,
        "08_people/collaboration_notes.md": lambda _: render_people(),
        "09_external/dependencies.md": render_dependencies,
        "10_testing/test_strategy.md": render_testing,
        "11_deployment/runtime_environment.md": render_runtime,
        "12_roadmap/next_steps_bootstrap.md": render_roadmap,
        "13_preferences/coding_style_inferred.md": render_style,
    }

    for rel, builder in writers.items():
        write_file(output_dir / rel, builder(analysis))

    manifest = {
        "generated_at": analysis["generated_at"],
        "project_root": analysis["project_root"],
        "output_dir": output_dir.as_posix(),
        "file_count": analysis["file_count"],
        "total_chars_scanned": analysis["total_chars_scanned"],
        "total_lines_scanned": analysis["total_lines_scanned"],
        "frameworks": analysis["frameworks"],
    }
    write_file(output_dir / "scan_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate RLM-friendly memory structure from raw project codebase (without using existing memory files)."
    )
    parser.add_argument("--project-root", required=True, help="Path to target project root")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for generated memory structure (default: <project-root>/memory/rlm_memory)",
    )
    parser.add_argument("--max-file-chars", type=int, default=160000, help="Max chars to read per file")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden folders/files (except hard ignored)")
    parser.add_argument(
        "--emit-json-graph",
        action="store_true",
        help="Emit module/dependency graph JSON (nodes + import edges).",
    )
    parser.add_argument(
        "--graph-file",
        default=None,
        help="Optional custom output path for graph JSON (default: <output-dir>/code_graph.json).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    if not project_root.exists() or not project_root.is_dir():
        raise SystemExit(f"Invalid --project-root: {project_root}")

    output_dir = Path(args.output_dir).resolve() if args.output_dir else (project_root / "memory" / "rlm_memory")
    output_dir.mkdir(parents=True, exist_ok=True)

    source_files = list(iter_source_files(project_root, args.include_hidden, args.max_file_chars))
    if not source_files:
        raise SystemExit("No source files found with configured suffix filters.")

    analysis = build_analysis(project_root, source_files)
    write_memory_structure(output_dir, analysis)

    if args.emit_json_graph:
        graph = build_json_graph(project_root, source_files, analysis["import_edges"])
        graph_file = Path(args.graph_file).resolve() if args.graph_file else (output_dir / "code_graph.json")
        write_file(graph_file, json.dumps(graph, ensure_ascii=False, indent=2))
        print(f"Graph JSON: {graph_file}")
        print(
            "Graph stats: "
            f"nodes={graph['stats']['nodes_total']} "
            f"edges={graph['stats']['edges_total']} "
            f"internal={graph['stats']['internal_edges']} "
            f"external={graph['stats']['external_edges']}"
        )

    print(f"Generated RLM memory structure at: {output_dir}")
    print(f"Scanned files: {analysis['file_count']}")
    print(f"Frameworks: {', '.join(analysis['frameworks']) if analysis['frameworks'] else '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
