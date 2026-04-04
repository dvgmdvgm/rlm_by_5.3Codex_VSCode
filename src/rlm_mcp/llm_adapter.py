"""Ollama LLM adapter with Gemma 4 best-practices.

Key behaviours:
  - Sampling: temperature=1.0, top_p=0.95, top_k=64 (fixed, per Gemma 4 spec).
  - Thinking mode: ``<|think|>`` is prepended to the system prompt so the model
    activates deep-reasoning.
  - Response parsing: thinking blocks ``<|channel>thought\\n…<channel|>`` are
    stripped automatically; callers receive only the final answer.
  - History sanitisation: ``strip_thinking_blocks()`` is exposed for multi-turn
    flows — previous assistant turns MUST NOT contain thinking blocks.
  - Multimodal ordering (future): images must precede text in the prompt.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field

import httpx


class LLMQueryError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Thinking-block parser
# ---------------------------------------------------------------------------

# Pattern: <|channel>thought\n ... <channel|>
# Greedy across newlines — captures the entire thinking block.
_THINKING_BLOCK_RE = re.compile(
    r"<\|channel>thought\s*\n.*?<channel\|>",
    re.DOTALL,
)


def strip_thinking_blocks(text: str) -> str:
    """Remove all ``<|channel>thought … <channel|>`` blocks from *text*.

    Used to sanitise assistant turns before feeding them back into a
    multi-turn conversation (Gemma 4 requirement: thinking blocks MUST
    NOT appear in chat history).
    """
    cleaned = _THINKING_BLOCK_RE.sub("", text)
    # Collapse leftover blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_final_answer(raw_response: str) -> str:
    """Extract only the final answer from a Gemma 4 response.

    If the response contains ``<|channel>thought … <channel|>`` blocks the
    block is removed and the remaining text (the final answer) is returned.
    If no thinking block is present the response is returned as-is.
    """
    return strip_thinking_blocks(raw_response)


def extract_thinking_block(raw_response: str) -> str:
    """Extract the raw thinking content from a Gemma 4 response.

    Returns the text *inside* ``<|channel>thought … <channel|>`` blocks
    (without the tags themselves). If no thinking block is present, returns
    an empty string.
    """
    blocks = _THINKING_BLOCK_RE.findall(raw_response)
    if not blocks:
        return ""
    # Strip the surrounding tags from each block and join
    parts: list[str] = []
    for block in blocks:
        # Remove opening tag+line and closing tag
        inner = re.sub(r"^<\|channel>thought\s*\n", "", block)
        inner = re.sub(r"<channel\|>$", "", inner)
        inner = inner.strip()
        if inner:
            parts.append(inner)
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# System-prompt wrapper
# ---------------------------------------------------------------------------

_THINKING_TAG = "<|think|>"


def prepend_thinking_tag(system_prompt: str) -> str:
    """Prepend ``<|think|>`` to *system_prompt* to activate Gemma 4 thinking mode."""
    if system_prompt.startswith(_THINKING_TAG):
        return system_prompt
    return f"{_THINKING_TAG}\n{system_prompt}"


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

@dataclass
class OllamaAdapter:
    base_url: str
    model: str
    timeout: float
    default_max_concurrency: int

    # --- Gemma 4 sampling defaults (overridable via config/env) ---
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 64

    # Whether to inject <|think|> and strip thinking blocks automatically.
    thinking_mode: bool = True

    # Last thinking block extracted from the model's response (debug/log use).
    # Updated on every query/query_async call. NOT persisted — callers can
    # read this after a query to save it themselves.
    _last_thinking: str = field(default="", init=False, repr=False)

    def __post_init__(self) -> None:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    # -- internal helpers --------------------------------------------------

    def _build_payload(self, prompt: str) -> dict:
        """Build the Ollama ``/api/generate`` JSON payload."""
        effective_prompt = prompt
        if self.thinking_mode:
            effective_prompt = prepend_thinking_tag(prompt)

        return {
            "model": self.model,
            "prompt": effective_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
            },
        }

    def _parse_response(self, data: dict) -> str:
        """Extract the answer text, stripping thinking blocks when enabled.

        Also stores the raw thinking block in ``_last_thinking`` for debug logging.
        """
        answer = data.get("response")
        if not isinstance(answer, str):
            raise LLMQueryError("Ollama response has no text field 'response'.")
        if self.thinking_mode:
            self._last_thinking = extract_thinking_block(answer)
            return extract_final_answer(answer)
        self._last_thinking = ""
        return answer

    @property
    def last_thinking(self) -> str:
        """The thinking block from the most recent query (empty if none)."""
        return self._last_thinking

    # -- public API --------------------------------------------------------

    def query(self, prompt: str) -> str:
        """Send *prompt* to Ollama and return the final answer (sync)."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json=self._build_payload(prompt),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise LLMQueryError(f"Ollama query failed: {exc}") from exc

        return self._parse_response(data)

    async def query_async(self, prompt: str) -> str:
        """Send *prompt* to Ollama and return the final answer (async)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=self._build_payload(prompt),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise LLMQueryError(f"Ollama query failed: {exc}") from exc

        return self._parse_response(data)

    async def query_many_async(
        self,
        prompts: list[str],
        max_concurrency: int | None = None,
    ) -> list[str]:
        limit = max_concurrency or self.default_max_concurrency
        semaphore = asyncio.Semaphore(limit)

        async def _one(prompt: str) -> str:
            async with semaphore:
                return await self.query_async(prompt)

        tasks = [_one(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)

    def query_many(
        self,
        prompts: list[str],
        max_concurrency: int | None = None,
    ) -> list[str]:
        return asyncio.run(self.query_many_async(prompts, max_concurrency=max_concurrency))
