"""Tests for mentor_engine module."""
from __future__ import annotations

import pytest

from rlm_mcp.intent_analyzer import TaskIntent
from rlm_mcp.mentor_engine import (
    MentorGuidance,
    build_mentor_prompt,
    parse_guidance,
    select_relevant_memory,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_intent() -> TaskIntent:
    return TaskIntent(
        task_category="new_feature",
        domain="backend",
        intent_summary="Add a new export endpoint for user data",
        preliminary_plan=["Create route", "Add serializer", "Write tests"],
        complexity="complex",
        raw_question="Add an export endpoint for user data",
    )


@pytest.fixture
def sample_memory_context() -> dict[str, str]:
    return {
        "canonical/architecture.md": "# Architecture\n\n## Backend\nUses Django REST framework with ModelViewSets.\n\n## Frontend\nVue 3 SPA.",
        "canonical/coding_rules.md": "# Coding Rules\n\n- All endpoints must have OpenAPI docstrings.\n- Use serializers for all responses.\n- Tests required for all new endpoints.",
        "canonical/active_tasks.md": "# Active Tasks\n\n### export_feature\n- [task][active;p=7] Export feature planned but not started.",
        "canonical/communication.md": "# Communication\n\n## Response language: ru\n## Style: structured, tables, emoji headers",
        "changelog/export_feature_decision.md": "# Export Decision\n\nDecided to use CSV format instead of XML. XML was too verbose.",
        "some/irrelevant/file.md": "This file has nothing to do with the task.",
    }


# ---------------------------------------------------------------------------
# select_relevant_memory
# ---------------------------------------------------------------------------

class TestSelectRelevantMemory:
    def test_canonical_files_always_selected(self, sample_intent, sample_memory_context):
        selected = select_relevant_memory(sample_intent, sample_memory_context)
        paths = [path for path, _ in selected]
        assert "canonical/architecture.md" in paths
        assert "canonical/coding_rules.md" in paths
        assert "canonical/active_tasks.md" in paths

    def test_irrelevant_files_filtered(self, sample_intent, sample_memory_context):
        selected = select_relevant_memory(sample_intent, sample_memory_context)
        paths = [path for path, _ in selected]
        assert "some/irrelevant/file.md" not in paths

    def test_respects_max_files(self, sample_intent, sample_memory_context):
        selected = select_relevant_memory(sample_intent, sample_memory_context, max_files=2)
        assert len(selected) <= 2

    def test_respects_max_chars(self, sample_intent, sample_memory_context):
        selected = select_relevant_memory(sample_intent, sample_memory_context, max_chars=100)
        total = sum(len(text) for _, text in selected)
        assert total <= 200  # Some leeway for partial chunks

    def test_empty_memory(self, sample_intent):
        selected = select_relevant_memory(sample_intent, {})
        assert selected == []


# ---------------------------------------------------------------------------
# build_mentor_prompt
# ---------------------------------------------------------------------------

class TestBuildMentorPrompt:
    def test_contains_intent(self, sample_intent):
        prompt = build_mentor_prompt(sample_intent, [("test.md", "test content")])
        assert "new_feature" in prompt
        assert "backend" in prompt
        assert "Add a new export endpoint" in prompt

    def test_contains_memory(self, sample_intent):
        snippets = [("rules.md", "Always test endpoints")]
        prompt = build_mentor_prompt(sample_intent, snippets)
        assert "Always test endpoints" in prompt
        assert "rules.md" in prompt

    def test_contains_plan(self, sample_intent):
        prompt = build_mentor_prompt(sample_intent, [])
        assert "Create route" in prompt
        assert "Add serializer" in prompt

    def test_contains_output_sections(self, sample_intent):
        prompt = build_mentor_prompt(sample_intent, [])
        assert "ARCHITECTURAL_PATTERNS" in prompt
        assert "MANDATORY_RULES" in prompt
        assert "ANTIPATTERNS_TO_AVOID" in prompt

    def test_code_index_included(self, sample_intent):
        prompt = build_mentor_prompt(
            sample_intent, [],
            code_index_summary={"total_files": 10, "total_symbols": 50, "languages": {"python": 10}},
        )
        assert "CODE INDEX SUMMARY" in prompt
        assert "10" in prompt

    def test_facts_included(self, sample_intent):
        facts = [{"value": {"type": "rule", "entity": "api_tests", "value": "All API endpoints must have tests", "priority": 9}}]
        prompt = build_mentor_prompt(sample_intent, [], fact_candidates=facts)
        assert "RELEVANT EXTRACTED FACTS" in prompt
        assert "api_tests" in prompt


# ---------------------------------------------------------------------------
# parse_guidance
# ---------------------------------------------------------------------------

class TestParseGuidance:
    def test_full_response(self):
        response = """\
## ARCHITECTURAL_PATTERNS
- Use Django REST ViewSets for all endpoints
- Follow repository pattern for data access

## MANDATORY_RULES
- All endpoints must have OpenAPI docstrings
- Use serializers for responses

## ANTIPATTERNS_TO_AVOID
- Do not use raw SQL queries — use ORM instead
- Avoid XML export — decided to use CSV (see changelog)

## HISTORICAL_CONTEXT
- Export feature was planned in sprint 3 but deferred

## IMPLEMENTATION_HINTS
- Use DRF's StreamingHttpResponse for large exports
- Add pagination for datasets > 1000 rows

## FILES_TO_INSPECT
- backend/views/export.py
- backend/serializers/user.py

## RISK_AREAS
- Large dataset exports may timeout
- CSV encoding issues with non-ASCII names
"""
        guidance = parse_guidance(response)
        assert len(guidance.architectural_patterns) == 2
        assert len(guidance.rules_to_follow) == 2
        assert len(guidance.antipatterns_to_avoid) == 2
        assert len(guidance.historical_context) == 1
        assert len(guidance.implementation_hints) == 2
        assert len(guidance.files_to_inspect) == 2
        assert len(guidance.risk_areas) == 2

    def test_partial_response(self):
        response = """\
## MANDATORY_RULES
- Test all code

## RISK_AREAS
- N/A
"""
        guidance = parse_guidance(response)
        assert len(guidance.rules_to_follow) == 1
        assert len(guidance.risk_areas) == 0  # N/A is filtered
        assert len(guidance.architectural_patterns) == 0

    def test_empty_response(self):
        guidance = parse_guidance("")
        assert len(guidance.rules_to_follow) == 0
        assert len(guidance.architectural_patterns) == 0

    def test_na_filtered(self):
        response = """\
## ARCHITECTURAL_PATTERNS
- N/A

## MANDATORY_RULES
- Follow the rules
"""
        guidance = parse_guidance(response)
        assert len(guidance.architectural_patterns) == 0
        assert len(guidance.rules_to_follow) == 1


# ---------------------------------------------------------------------------
# MentorGuidance
# ---------------------------------------------------------------------------

class TestMentorGuidance:
    def test_to_dict_strips_empty(self):
        guidance = MentorGuidance(
            rules_to_follow=["Rule 1"],
            architectural_patterns=[],
        )
        d = guidance.to_dict()
        assert "rules_to_follow" in d
        assert "architectural_patterns" not in d

    def test_to_instruction_prompt(self):
        guidance = MentorGuidance(
            rules_to_follow=["Always test", "Use type hints"],
            antipatterns_to_avoid=["No raw SQL"],
        )
        prompt = guidance.to_instruction_prompt()
        assert "MANDATORY RULES" in prompt
        assert "Always test" in prompt
        assert "ANTIPATTERNS TO AVOID" in prompt
        assert "No raw SQL" in prompt

    def test_empty_guidance_message(self):
        guidance = MentorGuidance()
        prompt = guidance.to_instruction_prompt()
        assert "No specific project guidance" in prompt
