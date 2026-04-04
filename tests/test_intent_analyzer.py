"""Tests for intent_analyzer module."""
from __future__ import annotations

import pytest

from rlm_mcp.intent_analyzer import (
    TaskIntent,
    build_intent,
    classify_domain,
    classify_task_category,
    assess_complexity,
)


# ---------------------------------------------------------------------------
# classify_task_category
# ---------------------------------------------------------------------------

class TestClassifyTaskCategory:
    def test_rewrite(self):
        assert classify_task_category("Rewrite the entire dashboard from scratch") == "rewrite"
        assert classify_task_category("Переписать с нуля") == "rewrite"

    def test_architecture(self):
        assert classify_task_category("Change the architecture pattern") == "architecture"
        assert classify_task_category("Новая парадигма взаимодействия") == "architecture"

    def test_memory_ops(self):
        assert classify_task_category("Consolidate the memory store") == "memory_ops"
        assert classify_task_category("Fix the canonical files") == "memory_ops"

    def test_ui_template(self):
        assert classify_task_category("Create a new page template") == "ui_template"
        assert classify_task_category("Измени макет страницы") == "ui_template"

    def test_symbol_lookup(self):
        assert classify_task_category("Find the function handle_request") == "symbol_lookup"
        assert classify_task_category("Найди функцию handle_request") == "symbol_lookup"

    def test_bugfix(self):
        assert classify_task_category("Fix the login bug") == "bugfix"
        assert classify_task_category("Исправь ошибку") == "bugfix"

    def test_refactor(self):
        assert classify_task_category("Refactor the config module") == "refactor"
        assert classify_task_category("Упрости этот код") == "refactor"

    def test_informational(self):
        assert classify_task_category("What is the purpose of this module?") == "informational"
        assert classify_task_category("Расскажи о проекте") == "informational"

    def test_new_feature(self):
        assert classify_task_category("Add a new export endpoint") == "new_feature"
        assert classify_task_category("Создай новый модуль") == "new_feature"

    def test_general_code_fallback(self):
        assert classify_task_category("process the data file") == "general_code"

    def test_empty_input(self):
        assert classify_task_category("") == "general_code"
        assert classify_task_category(None) == "general_code"


# ---------------------------------------------------------------------------
# classify_domain
# ---------------------------------------------------------------------------

class TestClassifyDomain:
    def test_memory_system(self):
        assert classify_domain("Update the RLM memory canonical files") == "memory_system"

    def test_frontend(self):
        assert classify_domain("Update the CSS styles for the layout") == "frontend"

    def test_backend(self):
        assert classify_domain("Add a new API endpoint") == "backend"

    def test_database(self):
        assert classify_domain("Create a migration for the users model") == "database"

    def test_devops(self):
        assert classify_domain("Configure the Docker deployment") == "devops"

    def test_testing(self):
        assert classify_domain("Write a test for the parser") == "testing"

    def test_full_stack_fallback(self):
        assert classify_domain("process the data") == "full_stack"


# ---------------------------------------------------------------------------
# assess_complexity
# ---------------------------------------------------------------------------

class TestAssessComplexity:
    def test_informational_always_simple(self):
        assert assess_complexity("What is X?", "informational") == "simple"

    def test_symbol_lookup_always_simple(self):
        assert assess_complexity("Find function Y", "symbol_lookup") == "simple"

    def test_architecture_always_complex(self):
        assert assess_complexity("Change it", "architecture") == "complex"

    def test_rewrite_always_complex(self):
        assert assess_complexity("Do it", "rewrite") == "complex"

    def test_short_question_simple(self):
        assert assess_complexity("Fix the bug", "bugfix") == "simple"

    def test_long_complex_question(self):
        long_q = " ".join(["word"] * 35) + " and then do more"
        assert assess_complexity(long_q, "new_feature") == "complex"

    def test_moderate_default(self):
        # 8 words → not below threshold, not complex either
        assert assess_complexity(
            "Refactor the config handler module to support plugins using dataclasses pattern",
            "refactor",
        ) == "moderate"


# ---------------------------------------------------------------------------
# build_intent
# ---------------------------------------------------------------------------

class TestBuildIntent:
    def test_auto_classification(self):
        intent = build_intent("Rewrite the dashboard from scratch")
        assert intent.task_category == "rewrite"
        assert intent.complexity == "complex"
        assert intent.raw_question == "Rewrite the dashboard from scratch"

    def test_cloud_override(self):
        intent = build_intent(
            "Do something",
            cloud_analysis={
                "task_category": "new_feature",
                "domain": "backend",
                "intent_summary": "Add REST endpoint",
                "preliminary_plan": ["Step 1", "Step 2"],
                "complexity": "complex",
            },
        )
        assert intent.task_category == "new_feature"
        assert intent.domain == "backend"
        assert intent.intent_summary == "Add REST endpoint"
        assert intent.preliminary_plan == ["Step 1", "Step 2"]
        assert intent.complexity == "complex"

    def test_partial_cloud_override(self):
        intent = build_intent(
            "Fix the login bug",
            cloud_analysis={"task_category": "bugfix"},
        )
        assert intent.task_category == "bugfix"
        # Domain should be auto-classified
        assert intent.domain in ("frontend", "backend", "full_stack", "memory_system", "testing", "database", "devops")

    def test_needs_mentor_simple(self):
        intent = build_intent("What is this?")
        assert intent.needs_mentor() is False

    def test_needs_mentor_complex(self):
        intent = build_intent("Rewrite the entire UI from scratch")
        assert intent.needs_mentor() is True

    def test_to_dict(self):
        intent = build_intent("Fix bug")
        d = intent.to_dict()
        assert "task_category" in d
        assert "domain" in d
        assert "raw_question" in d
