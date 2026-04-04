"""Mentor Engine — Local LLM deep-analysis pipeline.

Implements the "Intelligent Knowledge Mentor" role in the Role-Inversion
architecture. Receives a structured TaskIntent from the Cloud Strategist,
loads relevant project memory, performs deep reasoning via the local Sub-LM,
and returns a structured MentorGuidance — a ready-to-use "Guiding Prompt"
for the Cloud Executor.

Flow:
  TaskIntent → select_relevant_memory → build_mentor_prompt → local LLM → parse → MentorGuidance
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from .intent_analyzer import TaskIntent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Guidance data structure
# ---------------------------------------------------------------------------

@dataclass
class MentorGuidance:
    """Structured guidance returned by the Mentor to the Cloud Executor."""

    # Mandatory project patterns this task must follow
    architectural_patterns: list[str] = field(default_factory=list)
    # Hard rules from project memory
    rules_to_follow: list[str] = field(default_factory=list)
    # Approaches tried before and rejected (with reasons)
    antipatterns_to_avoid: list[str] = field(default_factory=list)
    # Past decisions relevant to this task
    historical_context: list[str] = field(default_factory=list)
    # Specific technical hints for implementation
    implementation_hints: list[str] = field(default_factory=list)
    # Files the executor should inspect
    files_to_inspect: list[str] = field(default_factory=list)
    # Potential pitfalls and edge cases
    risk_areas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Strip empty sections to save Cloud tokens
        return {k: v for k, v in d.items() if v}

    def to_instruction_prompt(self) -> str:
        """Render as a concise instruction prompt for the Cloud Executor."""
        sections: list[str] = []

        if self.architectural_patterns:
            items = "\n".join(f"  - {p}" for p in self.architectural_patterns)
            sections.append(f"**ARCHITECTURAL PATTERNS TO FOLLOW:**\n{items}")

        if self.rules_to_follow:
            items = "\n".join(f"  - {r}" for r in self.rules_to_follow)
            sections.append(f"**MANDATORY RULES:**\n{items}")

        if self.antipatterns_to_avoid:
            items = "\n".join(f"  - {a}" for a in self.antipatterns_to_avoid)
            sections.append(f"**ANTIPATTERNS TO AVOID:**\n{items}")

        if self.historical_context:
            items = "\n".join(f"  - {h}" for h in self.historical_context)
            sections.append(f"**HISTORICAL CONTEXT:**\n{items}")

        if self.implementation_hints:
            items = "\n".join(f"  - {h}" for h in self.implementation_hints)
            sections.append(f"**IMPLEMENTATION HINTS:**\n{items}")

        if self.files_to_inspect:
            items = "\n".join(f"  - {f}" for f in self.files_to_inspect)
            sections.append(f"**FILES TO INSPECT:**\n{items}")

        if self.risk_areas:
            items = "\n".join(f"  - {r}" for r in self.risk_areas)
            sections.append(f"**RISK AREAS:**\n{items}")

        if not sections:
            return "No specific project guidance found in memory for this task."

        return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Memory selection — intelligent context filtering
# ---------------------------------------------------------------------------

# Canonical files are always included (they're compact and central)
_CANONICAL_ALWAYS = (
    "canonical/architecture.md",
    "canonical/coding_rules.md",
    "canonical/active_tasks.md",
    "canonical/communication.md",
)

# Domain → preferred memory path prefixes (for non-canonical files)
_DOMAIN_PATH_HINTS: dict[str, list[str]] = {
    "frontend": ["template", "ui", "css", "style", "layout", "component", "view"],
    "backend": ["api", "server", "route", "endpoint", "model", "view"],
    "database": ["model", "migration", "schema", "sql", "orm"],
    "ui_ux": ["template", "ui", "design", "style", "component"],
    "devops": ["deploy", "docker", "ci", "pipeline", "build"],
    "memory_system": ["memory", "rlm", "mcp", "canonical", "consolidat"],
    "testing": ["test", "spec", "fixture"],
}

# Task category → extra memory selection logic
_TASK_EXTRA_CONTEXT: dict[str, list[str]] = {
    "bugfix": ["changelog/", "logs/"],
    "refactor": ["canonical/architecture", "changelog/"],
    "architecture": ["canonical/architecture", "changelog/"],
    "rewrite": ["canonical/coding_rules"],
    "new_feature": ["canonical/architecture", "canonical/coding_rules"],
    "memory_ops": ["canonical/", "logs/extracted_facts"],
}


def select_relevant_memory(
    intent: TaskIntent,
    memory_context: dict[str, str],
    *,
    max_chars: int = 12000,
    max_files: int = 12,
) -> list[tuple[str, str]]:
    """Select memory files most relevant to the task intent.

    Returns list of (path, content) tuples, ordered by relevance.
    Unlike the legacy keyword-matching, this uses intent metadata
    for intelligent selection.
    """
    scored: list[tuple[float, str, str]] = []

    domain_hints = _DOMAIN_PATH_HINTS.get(intent.domain, [])
    task_hints = _TASK_EXTRA_CONTEXT.get(intent.task_category, [])
    query_terms = _tokenize(intent.raw_question)

    for path, text in memory_context.items():
        score = _score_file(
            path=path,
            text=text,
            intent=intent,
            domain_hints=domain_hints,
            task_hints=task_hints,
            query_terms=query_terms,
        )
        if score > 0:
            scored.append((score, path, text))

    # Sort by relevance descending
    scored.sort(key=lambda row: -row[0])

    # Trim to budget
    result: list[tuple[str, str]] = []
    total_chars = 0
    for _, path, text in scored[:max_files]:
        chunk = text[:max_chars - total_chars] if total_chars + len(text) > max_chars else text
        if not chunk:
            break
        result.append((path, chunk))
        total_chars += len(chunk)
        if total_chars >= max_chars:
            break

    return result


def _score_file(
    *,
    path: str,
    text: str,
    intent: TaskIntent,
    domain_hints: list[str],
    task_hints: list[str],
    query_terms: set[str],
) -> float:
    """Score a memory file's relevance to the task intent."""
    score = 0.0
    lower_path = path.lower()
    lower_text = text[:2000].lower()  # Only scan beginning for speed

    # Canonical files always score high
    for canonical in _CANONICAL_ALWAYS:
        if canonical in lower_path:
            score += 10.0
            break

    # Domain-based boosting
    for hint in domain_hints:
        if hint in lower_path or hint in lower_text:
            score += 3.0

    # Task-category boosting
    for hint in task_hints:
        if hint in lower_path:
            score += 4.0

    # Query term matching (diminishing returns)
    if query_terms:
        hits = sum(1 for term in query_terms if term in lower_path or term in lower_text)
        score += min(hits * 1.5, 8.0)  # Cap at 8

    # Changelog relevance for bugfix/refactor
    if intent.task_category in ("bugfix", "refactor") and "changelog/" in lower_path:
        score += 2.0

    # Penalize archive/log noise
    if "_archive/" in lower_path or "logs/" in lower_path:
        score *= 0.3

    return score


def _tokenize(text: str) -> set[str]:
    return {part for part in re.findall(r"[a-zA-Zа-яА-Я0-9_]+", text.lower()) if len(part) > 2}


# ---------------------------------------------------------------------------
# Prompt construction — the Mentor's "reasoning frame"
# ---------------------------------------------------------------------------

_MENTOR_SYSTEM_PROMPT = """\
You are the project's **Intelligent Knowledge Mentor**. Your role is to analyze
the project's memory (rules, architecture, history, decisions) and produce a
focused, actionable guidance document for a Cloud AI that will execute the task.

IMPORTANT:
- Be factual. Only include items supported by the memory context below.
- Never fabricate rules, patterns, or history.
- If memory is insufficient for a section, write "N/A".
- Keep each item to 1-2 sentences maximum.
- Respond in English only.
- Output EXACTLY the sections listed below, each starting with the header line.

OUTPUT FORMAT (strict):

## ARCHITECTURAL_PATTERNS
- <pattern 1>
- <pattern 2>

## MANDATORY_RULES
- <rule 1>
- <rule 2>

## ANTIPATTERNS_TO_AVOID
- <antipattern 1 — reason>

## HISTORICAL_CONTEXT
- <past decision 1>

## IMPLEMENTATION_HINTS
- <hint 1>

## FILES_TO_INSPECT
- <file path 1>

## RISK_AREAS
- <risk 1>
"""


def build_mentor_prompt(
    intent: TaskIntent,
    memory_snippets: list[tuple[str, str]],
    *,
    code_index_summary: dict[str, Any] | None = None,
    fact_candidates: list[dict[str, Any]] | None = None,
) -> str:
    """Build the full prompt for the local LLM's deep reasoning phase."""

    # Intent block
    plan_text = ""
    if intent.preliminary_plan:
        plan_text = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(intent.preliminary_plan))
    else:
        plan_text = "  (Cloud did not provide a plan — infer from memory)"

    intent_block = (
        f"TASK INTENT:\n"
        f"  Category: {intent.task_category}\n"
        f"  Domain: {intent.domain}\n"
        f"  Complexity: {intent.complexity}\n"
        f"  Summary: {intent.intent_summary}\n"
        f"  Preliminary plan:\n{plan_text}\n"
    )

    # Memory context block
    memory_block = "PROJECT MEMORY CONTEXT:\n"
    for path, text in memory_snippets:
        memory_block += f"\n--- FILE: {path} ---\n{text}\n"

    # Code index block (optional)
    code_block = ""
    if code_index_summary:
        code_block = (
            f"\nCODE INDEX SUMMARY:\n"
            f"  Total files: {code_index_summary.get('total_files', '?')}\n"
            f"  Total symbols: {code_index_summary.get('total_symbols', '?')}\n"
            f"  Languages: {code_index_summary.get('languages', {})}\n"
        )

    # Extracted facts block (optional — most relevant facts pre-filtered)
    facts_block = ""
    if fact_candidates:
        facts_block = "\nRELEVANT EXTRACTED FACTS:\n"
        for fc in fact_candidates[:10]:
            v = fc.get("value", {})
            facts_block += (
                f"  - [{v.get('type','?')}] {v.get('entity','?')}: "
                f"{v.get('value','?')} (p={v.get('priority','?')})\n"
            )

    return (
        f"{_MENTOR_SYSTEM_PROMPT}\n"
        f"{intent_block}\n"
        f"{memory_block}\n"
        f"{code_block}"
        f"{facts_block}\n"
        f"Now analyze the memory and produce the guidance document.\n"
    )


# ---------------------------------------------------------------------------
# Response parsing — structured extraction from LLM output
# ---------------------------------------------------------------------------

_SECTION_HEADERS = {
    "ARCHITECTURAL_PATTERNS": "architectural_patterns",
    "MANDATORY_RULES": "rules_to_follow",
    "ANTIPATTERNS_TO_AVOID": "antipatterns_to_avoid",
    "HISTORICAL_CONTEXT": "historical_context",
    "IMPLEMENTATION_HINTS": "implementation_hints",
    "FILES_TO_INSPECT": "files_to_inspect",
    "RISK_AREAS": "risk_areas",
}


def parse_guidance(llm_response: str) -> MentorGuidance:
    """Parse the local LLM's structured output into MentorGuidance."""
    data: dict[str, list[str]] = {field: [] for field in _SECTION_HEADERS.values()}

    current_field: str | None = None

    for line in llm_response.splitlines():
        stripped = line.strip()

        # Detect section header
        for header, field_name in _SECTION_HEADERS.items():
            if header in stripped.upper().replace(" ", "_"):
                current_field = field_name
                break
        else:
            # Parse bullet items
            if current_field and stripped.startswith("-"):
                item = stripped.lstrip("-").strip()
                if item and item.upper() != "N/A":
                    data[current_field].append(item)

    return MentorGuidance(**data)


# ---------------------------------------------------------------------------
# Main pipeline — orchestrates the full Mentor flow
# ---------------------------------------------------------------------------

def generate_guidance(
    *,
    intent: TaskIntent,
    memory_context: dict[str, str],
    llm_adapter: Any,
    code_index_summary: dict[str, Any] | None = None,
    fact_candidates: list[dict[str, Any]] | None = None,
    max_memory_chars: int = 12000,
    max_memory_files: int = 12,
) -> MentorGuidance:
    """Full Mentor pipeline: select memory → build prompt → query LLM → parse.

    Parameters
    ----------
    intent : TaskIntent
        Structured intent from the Cloud Strategist.
    memory_context : dict[str, str]
        Full memory file map from MemoryStore.
    llm_adapter : OllamaAdapter
        Local LLM adapter for deep reasoning.
    code_index_summary : dict, optional
        Compact code index summary.
    fact_candidates : list[dict], optional
        Pre-filtered extracted facts relevant to the query.
    max_memory_chars : int
        Token budget for memory context in the prompt.
    max_memory_files : int
        Maximum number of memory files to include.

    Returns
    -------
    MentorGuidance
        Structured guidance for the Cloud Executor.
    """
    # Step 1: Select relevant memory
    snippets = select_relevant_memory(
        intent,
        memory_context,
        max_chars=max_memory_chars,
        max_files=max_memory_files,
    )

    # Step 2: Build the mentor prompt
    prompt = build_mentor_prompt(
        intent,
        snippets,
        code_index_summary=code_index_summary,
        fact_candidates=fact_candidates,
    )

    # Step 3: Query local LLM
    logger.info(
        "Mentor generating guidance for [%s/%s] — %d memory files, prompt ~%d chars",
        intent.task_category, intent.domain, len(snippets), len(prompt),
    )
    raw_response = llm_adapter.query(prompt)

    # Step 4: Parse structured output
    guidance = parse_guidance(raw_response)

    logger.info(
        "Mentor produced: %d patterns, %d rules, %d antipatterns, %d hints",
        len(guidance.architectural_patterns),
        len(guidance.rules_to_follow),
        len(guidance.antipatterns_to_avoid),
        len(guidance.implementation_hints),
    )

    return guidance
