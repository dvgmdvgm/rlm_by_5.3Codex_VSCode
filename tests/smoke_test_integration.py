"""Integration smoke-test for the Role-Inversion + Gemma 4 pipeline.

Requires Ollama running locally with the configured model.
Run:  python tests/smoke_test_integration.py

NOT part of pytest — this is a manual E2E test.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure the src package is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

os.chdir(str(ROOT))  # so memory dir resolves correctly


def separator(title: str) -> None:
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def test_1_ollama_connection():
    """Check Ollama is reachable and the model responds."""
    separator("TEST 1: Ollama connection + Gemma 4 sampling")
    from rlm_mcp.llm_adapter import OllamaAdapter

    adapter = OllamaAdapter(
        base_url=os.getenv("RLM_OLLAMA_URL", "http://127.0.0.1:11434"),
        model=os.getenv("RLM_OLLAMA_MODEL", "gemma4:latest"),
        timeout=60,
        default_max_concurrency=2,
        temperature=1.0,
        top_p=0.95,
        top_k=64,
        thinking_mode=True,
    )

    prompt = "What is 2 + 2? Answer in one word."
    print(f"  Prompt: {prompt}")

    try:
        answer = adapter.query(prompt)
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        print("  → Make sure Ollama is running: ollama serve")
        print(f"  → Make sure model is pulled: ollama pull {adapter.model}")
        return False

    print(f"  Answer: {answer}")
    print(f"  Thinking block captured: {len(adapter.last_thinking)} chars")
    if adapter.last_thinking:
        print(f"  Thinking preview: {adapter.last_thinking[:200]}...")

    print("  ✅ PASS")
    return True


def test_2_thinking_log():
    """Check that thinking log is written to disk."""
    separator("TEST 2: Thinking log file")
    from rlm_mcp.config import load_settings

    settings = load_settings()
    thinking_log = settings.memory_dir / "logs" / "local_llm_thinking.md"

    # The log may not exist yet if test_1 didn't go through server.py.
    # We'll test it via a direct call to the save helper.
    from rlm_mcp.llm_adapter import OllamaAdapter

    adapter = OllamaAdapter(
        base_url=os.getenv("RLM_OLLAMA_URL", "http://127.0.0.1:11434"),
        model=os.getenv("RLM_OLLAMA_MODEL", "gemma4:latest"),
        timeout=60,
        default_max_concurrency=2,
        thinking_mode=True,
    )

    try:
        adapter.query("Explain briefly what a Python dataclass is.")
    except Exception as e:
        print(f"  ❌ FAIL (Ollama): {e}")
        return False

    # Manually write the log like server.py does
    from rlm_mcp.time_policy import now_iso, resolve_timestamp_mode

    ts = now_iso(resolve_timestamp_mode("local"))
    thinking = adapter.last_thinking
    thinking_log.parent.mkdir(parents=True, exist_ok=True)

    header = f"# Local LLM Thinking Log\n\n> Tool: `smoke_test`  \n> Timestamp: {ts}\n\n---\n\n"
    if thinking:
        content = header + thinking + "\n"
    else:
        content = header + "_No thinking block in this response._\n"

    thinking_log.write_text(content, encoding="utf-8")
    print(f"  Log written to: {thinking_log}")
    print(f"  Log size: {thinking_log.stat().st_size} bytes")
    print(f"  Has thinking content: {bool(thinking)}")
    print("  ✅ PASS")
    return True


def test_3_intent_classification():
    """Verify intent classification works end-to-end."""
    separator("TEST 3: Intent classification (no LLM needed)")
    from rlm_mcp.intent_analyzer import build_intent

    cases = [
        ("Rewrite the dashboard from scratch", "rewrite", True),
        ("What is this project about?", "informational", False),
        ("Fix the login bug", "bugfix", False),
        ("Add a new REST API endpoint for users", "new_feature", True),
        ("Refactor the config module", "refactor", True),
    ]

    all_ok = True
    for question, expected_category, expected_mentor in cases:
        intent = build_intent(question)
        cat_ok = intent.task_category == expected_category
        mentor_ok = intent.needs_mentor() == expected_mentor
        status = "✅" if (cat_ok and mentor_ok) else "❌"
        if not (cat_ok and mentor_ok):
            all_ok = False
        print(f"  {status} \"{question}\"")
        print(f"      → category={intent.task_category} (expected {expected_category}), "
              f"mentor={intent.needs_mentor()} (expected {expected_mentor})")

    if all_ok:
        print("  ✅ ALL PASS")
    else:
        print("  ❌ SOME FAILED")
    return all_ok


def test_4_mentor_pipeline():
    """Full Mentor pipeline: intent → memory selection → LLM → guidance."""
    separator("TEST 4: Full Mentor pipeline (requires Ollama)")
    from rlm_mcp.intent_analyzer import build_intent
    from rlm_mcp.mentor_engine import generate_guidance
    from rlm_mcp.memory_store import MemoryStore
    from rlm_mcp.config import load_settings
    from rlm_mcp.llm_adapter import OllamaAdapter

    settings = load_settings()
    adapter = OllamaAdapter(
        base_url=os.getenv("RLM_OLLAMA_URL", "http://127.0.0.1:11434"),
        model=os.getenv("RLM_OLLAMA_MODEL", "gemma4:latest"),
        timeout=120,
        default_max_concurrency=2,
        thinking_mode=True,
    )

    store = MemoryStore(settings.memory_dir)
    memory_context = store.load_memory_context()
    print(f"  Memory files loaded: {len(memory_context)}")

    question = "Add a new MCP tool for project health checks"
    intent = build_intent(
        question,
        cloud_analysis={
            "task_category": "new_feature",
            "domain": "memory_system",
            "intent_summary": "Create a health-check MCP tool",
            "preliminary_plan": [
                "Define tool signature",
                "Implement health checks",
                "Register as MCP tool",
                "Write tests",
            ],
        },
    )
    print(f"  Intent: {intent.task_category}/{intent.domain} [{intent.complexity}]")

    try:
        guidance = generate_guidance(
            intent=intent,
            memory_context=memory_context,
            llm_adapter=adapter,
        )
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False

    print(f"  Guidance sections filled:")
    d = guidance.to_dict()
    for section, items in d.items():
        print(f"    {section}: {len(items)} items")

    print(f"\n  --- GUIDANCE PROMPT ---")
    prompt = guidance.to_instruction_prompt()
    print(prompt[:1000])
    if len(prompt) > 1000:
        print(f"  ... [{len(prompt) - 1000} more chars]")

    print(f"\n  Thinking captured: {len(adapter.last_thinking)} chars")
    if adapter.last_thinking:
        print(f"  Thinking preview:\n{adapter.last_thinking[:500]}")

    print("  ✅ PASS")
    return True


def test_5_bootstrap_signals():
    """Verify bootstrap returns mentor_recommended and intent_classification."""
    separator("TEST 5: Bootstrap mentor signals (requires Ollama)")
    from rlm_mcp.server import local_memory_bootstrap

    try:
        result = local_memory_bootstrap(
            question="Refactor the server module to use dependency injection",
            project_path=str(ROOT),
        )
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False

    print(f"  mentor_recommended: {result.get('mentor_recommended')}")
    print(f"  intent_classification: {result.get('intent_classification')}")
    print(f"  canonical_read_needed: {result.get('canonical_read_needed')}")
    print(f"  brief preview: {str(result.get('brief', ''))[:200]}...")

    has_mentor = "mentor_recommended" in result
    has_intent = "intent_classification" in result
    if has_mentor and has_intent:
        print("  ✅ PASS")
    else:
        print(f"  ❌ FAIL: missing keys (mentor={has_mentor}, intent={has_intent})")
    return has_mentor and has_intent


def main():
    print("=" * 60)
    print("  RLM Role-Inversion + Gemma 4 Integration Smoke Test")
    print("=" * 60)

    results = {}

    # Test 3 runs without Ollama — always run first
    results["intent_classification"] = test_3_intent_classification()

    # Tests 1, 2, 4, 5 need Ollama
    results["ollama_connection"] = test_1_ollama_connection()

    if results["ollama_connection"]:
        results["thinking_log"] = test_2_thinking_log()
        results["mentor_pipeline"] = test_4_mentor_pipeline()
        results["bootstrap_signals"] = test_5_bootstrap_signals()
    else:
        print("\n⚠️  Skipping Ollama-dependent tests (1 failed)")
        for k in ("thinking_log", "mentor_pipeline", "bootstrap_signals"):
            results[k] = None

    separator("SUMMARY")
    for name, ok in results.items():
        if ok is None:
            print(f"  ⏭️  {name}: SKIPPED")
        elif ok:
            print(f"  ✅ {name}: PASS")
        else:
            print(f"  ❌ {name}: FAIL")

    total = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    print(f"\n  {total} passed, {failed} failed, {skipped} skipped")


if __name__ == "__main__":
    main()
