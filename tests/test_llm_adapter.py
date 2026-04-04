"""Tests for llm_adapter Gemma 4 best-practices."""
from __future__ import annotations

import pytest

from rlm_mcp.llm_adapter import (
    OllamaAdapter,
    extract_final_answer,
    extract_thinking_block,
    prepend_thinking_tag,
    strip_thinking_blocks,
)


# ---------------------------------------------------------------------------
# strip_thinking_blocks / extract_final_answer
# ---------------------------------------------------------------------------

class TestStripThinkingBlocks:
    """Gemma 4 thinking-block parser."""

    def test_removes_single_thinking_block(self):
        raw = (
            "<|channel>thought\n"
            "Let me analyze this step by step...\n"
            "First, I need to check the architecture.\n"
            "<channel|>\n"
            "The answer is 42."
        )
        assert strip_thinking_blocks(raw) == "The answer is 42."

    def test_removes_multiple_thinking_blocks(self):
        raw = (
            "<|channel>thought\nThinking part 1\n<channel|>\n"
            "Middle text.\n"
            "<|channel>thought\nThinking part 2\n<channel|>\n"
            "Final text."
        )
        result = strip_thinking_blocks(raw)
        assert "Thinking part 1" not in result
        assert "Thinking part 2" not in result
        assert "Middle text." in result
        assert "Final text." in result

    def test_no_thinking_block_passthrough(self):
        raw = "Just a normal response without thinking."
        assert strip_thinking_blocks(raw) == raw

    def test_empty_string(self):
        assert strip_thinking_blocks("") == ""

    def test_thinking_block_with_code(self):
        raw = (
            "<|channel>thought\n"
            "```python\ndef foo(): pass\n```\n"
            "I should use a different approach.\n"
            "<channel|>\n"
            "Use `bar()` instead of `foo()`."
        )
        result = strip_thinking_blocks(raw)
        assert "def foo" not in result
        assert "Use `bar()` instead of `foo()`." == result

    def test_thinking_block_multiline_complex(self):
        raw = (
            "<|channel>thought\n"
            "Step 1: Read architecture.md\n"
            "Step 2: Check coding_rules.md\n"
            "Step 3: Analyze patterns\n"
            "\n"
            "The project uses Django REST framework.\n"
            "Historical note: XML was rejected in favor of CSV.\n"
            "<channel|>\n"
            "\n"
            "## ARCHITECTURAL_PATTERNS\n"
            "- Use Django REST ViewSets\n"
        )
        result = strip_thinking_blocks(raw)
        assert "Step 1" not in result
        assert "## ARCHITECTURAL_PATTERNS" in result
        assert "Use Django REST ViewSets" in result

    def test_collapses_excessive_newlines(self):
        raw = (
            "<|channel>thought\nthinking\n<channel|>\n"
            "\n\n\n\n\n"
            "Final answer."
        )
        result = strip_thinking_blocks(raw)
        # Should have at most 2 consecutive newlines
        assert "\n\n\n" not in result
        assert "Final answer." in result


class TestExtractFinalAnswer:
    """extract_final_answer is a thin wrapper over strip_thinking_blocks."""

    def test_with_thinking(self):
        raw = "<|channel>thought\nreasoning\n<channel|>\nThe answer."
        assert extract_final_answer(raw) == "The answer."

    def test_without_thinking(self):
        raw = "Plain answer."
        assert extract_final_answer(raw) == "Plain answer."


class TestExtractThinkingBlock:
    """extract_thinking_block extracts the raw thinking content."""

    def test_single_block(self):
        raw = (
            "<|channel>thought\n"
            "Step 1: Check rules.\n"
            "Step 2: Analyze patterns.\n"
            "<channel|>\n"
            "The final answer."
        )
        thinking = extract_thinking_block(raw)
        assert "Step 1: Check rules." in thinking
        assert "Step 2: Analyze patterns." in thinking
        assert "<|channel>" not in thinking
        assert "<channel|>" not in thinking
        assert "The final answer" not in thinking

    def test_no_thinking_block(self):
        raw = "Just a plain response."
        assert extract_thinking_block(raw) == ""

    def test_empty_string(self):
        assert extract_thinking_block("") == ""

    def test_multiple_blocks(self):
        raw = (
            "<|channel>thought\nFirst reasoning.\n<channel|>\n"
            "Middle.\n"
            "<|channel>thought\nSecond reasoning.\n<channel|>\n"
            "End."
        )
        thinking = extract_thinking_block(raw)
        assert "First reasoning." in thinking
        assert "Second reasoning." in thinking


# ---------------------------------------------------------------------------
# prepend_thinking_tag
# ---------------------------------------------------------------------------

class TestPrependThinkingTag:
    def test_adds_tag(self):
        result = prepend_thinking_tag("You are a helpful assistant.")
        assert result.startswith("<|think|>")
        assert "You are a helpful assistant." in result

    def test_idempotent(self):
        tagged = "<|think|>\nYou are a helpful assistant."
        assert prepend_thinking_tag(tagged) == tagged

    def test_empty_prompt(self):
        result = prepend_thinking_tag("")
        assert result.startswith("<|think|>")


# ---------------------------------------------------------------------------
# OllamaAdapter._build_payload
# ---------------------------------------------------------------------------

class TestBuildPayload:
    """Verify the adapter builds correct Ollama payloads."""

    @pytest.fixture
    def adapter(self) -> OllamaAdapter:
        return OllamaAdapter(
            base_url="http://localhost:11434",
            model="gemma4:27b",
            timeout=120,
            default_max_concurrency=4,
            temperature=1.0,
            top_p=0.95,
            top_k=64,
            thinking_mode=True,
        )

    @pytest.fixture
    def adapter_no_thinking(self) -> OllamaAdapter:
        return OllamaAdapter(
            base_url="http://localhost:11434",
            model="gemma4:27b",
            timeout=120,
            default_max_concurrency=4,
            thinking_mode=False,
        )

    def test_includes_sampling_params(self, adapter: OllamaAdapter):
        payload = adapter._build_payload("Hello")
        assert payload["options"]["temperature"] == 1.0
        assert payload["options"]["top_p"] == 0.95
        assert payload["options"]["top_k"] == 64

    def test_thinking_mode_prepends_tag(self, adapter: OllamaAdapter):
        payload = adapter._build_payload("Analyze this code")
        assert payload["prompt"].startswith("<|think|>")
        assert "Analyze this code" in payload["prompt"]

    def test_no_thinking_mode_no_tag(self, adapter_no_thinking: OllamaAdapter):
        payload = adapter_no_thinking._build_payload("Analyze this code")
        assert not payload["prompt"].startswith("<|think|>")
        assert payload["prompt"] == "Analyze this code"

    def test_stream_false(self, adapter: OllamaAdapter):
        payload = adapter._build_payload("test")
        assert payload["stream"] is False

    def test_model_set(self, adapter: OllamaAdapter):
        payload = adapter._build_payload("test")
        assert payload["model"] == "gemma4:27b"


# ---------------------------------------------------------------------------
# OllamaAdapter._parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:
    @pytest.fixture
    def adapter(self) -> OllamaAdapter:
        return OllamaAdapter(
            base_url="http://localhost:11434",
            model="gemma4:27b",
            timeout=120,
            default_max_concurrency=4,
            thinking_mode=True,
        )

    @pytest.fixture
    def adapter_no_thinking(self) -> OllamaAdapter:
        return OllamaAdapter(
            base_url="http://localhost:11434",
            model="gemma4:27b",
            timeout=120,
            default_max_concurrency=4,
            thinking_mode=False,
        )

    def test_strips_thinking_in_thinking_mode(self, adapter: OllamaAdapter):
        data = {
            "response": (
                "<|channel>thought\nInternal reasoning here.\n<channel|>\n"
                "The final answer."
            )
        }
        result = adapter._parse_response(data)
        assert result == "The final answer."
        assert adapter.last_thinking == "Internal reasoning here."

    def test_passthrough_when_thinking_off(self, adapter_no_thinking: OllamaAdapter):
        raw = "<|channel>thought\nInternal reasoning here.\n<channel|>\nThe final answer."
        data = {"response": raw}
        assert adapter_no_thinking._parse_response(data) == raw
        assert adapter_no_thinking.last_thinking == ""

    def test_last_thinking_empty_when_no_block(self, adapter: OllamaAdapter):
        data = {"response": "No thinking block here."}
        adapter._parse_response(data)
        assert adapter.last_thinking == ""

    def test_raises_on_missing_response(self, adapter: OllamaAdapter):
        with pytest.raises(Exception, match="no text field"):
            adapter._parse_response({"model": "gemma4"})

    def test_raises_on_non_string_response(self, adapter: OllamaAdapter):
        with pytest.raises(Exception, match="no text field"):
            adapter._parse_response({"response": 42})


# ---------------------------------------------------------------------------
# History sanitisation (multi-turn)
# ---------------------------------------------------------------------------

class TestHistorySanitisation:
    """Validate that strip_thinking_blocks can sanitise multi-turn history."""

    def test_sanitise_assistant_turn(self):
        """Simulate cleaning an assistant turn before adding to history."""
        assistant_response = (
            "<|channel>thought\n"
            "The user wants to refactor the config module.\n"
            "I should check coding_rules.md for naming conventions.\n"
            "<channel|>\n"
            "Here is the refactored config:\n"
            "```python\n@dataclass\nclass Config: ...\n```"
        )
        clean = strip_thinking_blocks(assistant_response)
        assert "<|channel>" not in clean
        assert "thought" not in clean or "thought" in "Here is the refactored"
        assert "refactored config" in clean
        assert "@dataclass" in clean

    def test_multiple_turns_cleaned(self):
        """Validate batch sanitisation of a conversation history."""
        turns = [
            "<|channel>thought\nAnalyzing...\n<channel|>\nAnswer 1.",
            "<|channel>thought\nMore analysis...\n<channel|>\nAnswer 2.",
            "Answer 3 (no thinking).",
        ]
        cleaned = [strip_thinking_blocks(t) for t in turns]
        assert cleaned == ["Answer 1.", "Answer 2.", "Answer 3 (no thinking)."]
