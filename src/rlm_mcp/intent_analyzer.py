"""Intent Analyzer — deterministic classification of user requests.

Runs server-side (no LLM calls). Provides structured intent metadata
that the Mentor Engine uses to select relevant memory and guide the
local Sub-LM reasoning.

Role-Inversion Architecture:
  Cloud (Strategist) → classifies → sends intent → Local (Mentor) → guidance → Cloud (Executor)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any


# ---------------------------------------------------------------------------
# Task categories (superset of legacy _classify_task_type values)
# ---------------------------------------------------------------------------
TASK_CATEGORIES = {
    "new_feature",
    "refactor",
    "bugfix",
    "analysis",
    "architecture",
    "devops",
    "docs",
    "rewrite",
    "ui_template",
    "symbol_lookup",
    "informational",
    "general_code",
    "memory_ops",
}

# ---------------------------------------------------------------------------
# Domain layers
# ---------------------------------------------------------------------------
DOMAINS = {
    "frontend",
    "backend",
    "database",
    "ui_ux",
    "devops",
    "full_stack",
    "memory_system",
    "testing",
    "docs",
}


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------
@dataclass
class TaskIntent:
    """Structured representation of the Cloud Strategist's analysis."""

    task_category: str
    domain: str
    intent_summary: str
    preliminary_plan: list[str] = field(default_factory=list)
    complexity: str = "moderate"  # simple | moderate | complex
    raw_question: str = ""
    cloud_metadata: dict[str, Any] = field(default_factory=dict)

    # Convenience -----------------------------------------------------------
    def needs_mentor(self) -> bool:
        """Return True when the task is complex enough to warrant a mentor pass."""
        if self.complexity == "simple":
            return False
        if self.task_category in ("informational", "symbol_lookup"):
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Classification helpers (keyword-based, deterministic, no LLM)
# ---------------------------------------------------------------------------

_REWRITE_MARKERS = (
    "rewrite", "from scratch", "ground-up", "ground up", "rework",
    "full rewrite", "start over", "rebuild", "new implementation",
    "с нуля", "переписать", "переписыва", "переделать", "переделыва",
    "заново", "полная переделка", "полный рерайт",
)
_UI_MARKERS = (
    "template", "layout", "design", "style", "css", "html", "page",
    "screen", "component", "ui", "ux", "profile", "markup", "view",
    "шаблон", "макет", "дизайн", "стил", "страниц", "экран", "верст",
    "профил", "компонент", "интерфейс",
)
_SYMBOL_MARKERS = (
    "symbol", "function", "class", "method", "implementation",
    "where is", "find symbol", "find function", "найди функцию",
    "найди класс", "символ", "реализац", "метод",
)
_BUGFIX_MARKERS = (
    "fix", "bug", "error", "broken", "issue", "crash", "not working",
    "regression", "исправ", "баг", "ошиб", "не работает", "слом",
)
_REFACTOR_MARKERS = (
    "refactor", "cleanup", "simplify", "restructure", "optimize",
    "рефактор", "упрост", "оптимиз", "перестро",
)
_INFO_MARKERS = (
    "what is", "about", "describe", "explain", "overview", "summary",
    "tell me", "how does", "how do", "purpose", "что это", "о чём",
    "о чем", "расскажи", "опиши", "объясни", "зачем", "для чего",
    "как работает", "what does", "what are",
)
_FEATURE_MARKERS = (
    "add", "create", "implement", "build", "make", "new",
    "добав", "создай", "реализуй", "построй", "сделай", "нов",
)
_ARCH_MARKERS = (
    "architecture", "design pattern", "paradigm", "инверси", "парадигм",
    "архитектур", "паттерн", "концеп", "workflow", "pipeline",
)
_DEVOPS_MARKERS = (
    "deploy", "docker", "ci", "cd", "pipeline", "github actions",
    "build system", "деплой", "развёрт", "сборк",
)
_DOCS_MARKERS = (
    "document", "readme", "docs", "write doc", "документ", "ридми",
)
_MEMORY_MARKERS = (
    "memory", "consolidat", "extracted_fact", "canonical", "bootstrap",
    "память", "консолид", "канонич",
)

# ---------------------------------------------------------------------------
# Domain detection
# ---------------------------------------------------------------------------
_FRONTEND_MARKERS = (
    "frontend", "html", "css", "template", "layout", "style", "page",
    "component", "react", "vue", "svelte", "angular", "ui", "ux",
    "фронтенд", "шаблон", "верстк", "макет", "компонент",
)
_BACKEND_MARKERS = (
    "backend", "server", "api", "endpoint", "route", "django", "flask",
    "fastapi", "express", "бэкенд", "серверн", "маршрут",
)
_DB_MARKERS = (
    "database", "sql", "query", "model", "migration", "orm",
    "база данных", "запрос", "миграц", "модел",
)
_DEVOPS_DOMAIN_MARKERS = (
    "docker", "deploy", "ci", "cd", "kubernetes", "k8s", "nginx",
    "деплой", "контейнер",
)
_TESTING_MARKERS = (
    "test", "spec", "assert", "mock", "fixture", "тест",
)
_MEMORY_DOMAIN_MARKERS = (
    "memory", "rlm", "mcp", "consolidat", "bootstrap", "canonical",
    "память", "консолид", "канонич",
)


def _any_match(text: str, markers: tuple[str, ...]) -> bool:
    return any(m in text for m in markers)


def classify_task_category(question: str) -> str:
    """Classify the user question into a task category (deterministic)."""
    q = (question or "").lower()

    if _any_match(q, _REWRITE_MARKERS):
        return "rewrite"
    if _any_match(q, _ARCH_MARKERS):
        return "architecture"
    if _any_match(q, _MEMORY_MARKERS):
        return "memory_ops"
    if _any_match(q, _UI_MARKERS):
        return "ui_template"
    if _any_match(q, _SYMBOL_MARKERS):
        return "symbol_lookup"
    if _any_match(q, _BUGFIX_MARKERS):
        return "bugfix"
    if _any_match(q, _REFACTOR_MARKERS):
        return "refactor"
    if _any_match(q, _DEVOPS_MARKERS):
        return "devops"
    if _any_match(q, _DOCS_MARKERS):
        return "docs"
    if _any_match(q, _FEATURE_MARKERS):
        return "new_feature"
    if _any_match(q, _INFO_MARKERS):
        return "informational"
    return "general_code"


def classify_domain(question: str) -> str:
    """Classify the user question into a domain/layer (deterministic)."""
    q = (question or "").lower()

    if _any_match(q, _MEMORY_DOMAIN_MARKERS):
        return "memory_system"
    if _any_match(q, _FRONTEND_MARKERS):
        return "frontend"
    if _any_match(q, _BACKEND_MARKERS):
        return "backend"
    if _any_match(q, _DB_MARKERS):
        return "database"
    if _any_match(q, _DEVOPS_DOMAIN_MARKERS):
        return "devops"
    if _any_match(q, _TESTING_MARKERS):
        return "testing"
    return "full_stack"


def assess_complexity(question: str, task_category: str) -> str:
    """Assess task complexity to decide if mentor pass is warranted."""
    # Simple categories that don't need deep reasoning
    if task_category in ("informational", "symbol_lookup", "docs"):
        return "simple"

    q = (question or "").lower()
    word_count = len(q.split())

    # Short questions are usually simple
    if word_count < 8 and task_category not in ("architecture", "rewrite"):
        return "simple"

    # Architecture, rewrite, full rewrites are always complex
    if task_category in ("architecture", "rewrite"):
        return "complex"

    # Multi-step indicators
    complex_signals = (
        "and then", "after that", "also", "потом", "затем", "также",
        "а ещё", "и ещё", "плюс", "additionally", "furthermore",
        "multiple", "several", "несколько", "множеств",
    )
    if _any_match(q, complex_signals):
        return "complex"

    # Long questions with code-changing intent
    if word_count > 30 and task_category in ("new_feature", "refactor", "bugfix"):
        return "complex"

    return "moderate"


def build_intent(
    question: str,
    *,
    cloud_analysis: dict[str, Any] | None = None,
) -> TaskIntent:
    """Build a TaskIntent from a user question and optional Cloud analysis.

    If the Cloud already classified the task (via cloud_analysis), use those
    values. Otherwise, classify server-side (deterministic).
    """
    cloud = cloud_analysis or {}

    task_category = cloud.get("task_category") or classify_task_category(question)
    domain = cloud.get("domain") or classify_domain(question)
    complexity = cloud.get("complexity") or assess_complexity(question, task_category)
    intent_summary = cloud.get("intent_summary", "")
    preliminary_plan = cloud.get("preliminary_plan", [])

    # If Cloud didn't provide a summary, generate a minimal one
    if not intent_summary:
        intent_summary = _auto_summarize(question, task_category)

    return TaskIntent(
        task_category=task_category,
        domain=domain,
        intent_summary=intent_summary,
        preliminary_plan=preliminary_plan,
        complexity=complexity,
        raw_question=question,
        cloud_metadata=cloud,
    )


def _auto_summarize(question: str, task_category: str) -> str:
    """Generate a minimal intent summary from the question (no LLM)."""
    # Take first ~100 chars as a rough summary
    clean = re.sub(r"\s+", " ", question).strip()
    if len(clean) > 120:
        clean = clean[:120] + "..."
    return f"[{task_category}] {clean}"
