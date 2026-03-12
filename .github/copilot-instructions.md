# Copilot Instructions — RLM Memory Autopilot

## ⛔ HARD GATE — MEMORY BOOTSTRAP (runs FIRST on EVERY message)

Before ANY response: call `local_memory_bootstrap(question=<user_task>, project_path=<workspace_root>)` and WAIT for result.
**No exceptions.** Not for simple questions. Not for follow-ups. Not ever.

---

## Slash Commands

- `/orchestrate` (or explicit reference to `orchestrate.prompt.md`): invoke `.github/prompts/orchestrator_skill.prompt.md`, delegate to subagents only. Orchestrator is a state-machine manager — it MUST NOT code directly. When orchestration is active, sections B/C below are SUSPENDED (handled by worker/synthesizer/archivist subagents). If planner delegation fails, return `ORCHESTRATOR_NOT_AVAILABLE` and STOP.

---

## Memory Workflow

### A) Before work (always)

1. Use `brief` from bootstrap as primary context. Respect `user_response_language`.
2. **If `canonical_read_needed` is `false`** in bootstrap → do NOT read canonical files. The brief is sufficient.
3. Only if brief is insufficient or contradictory, read canonical: `architecture.md`, `coding_rules.md`, `active_tasks.md`.
4. When `code_index_summary` present → prefer `search_code_symbols` / `get_code_symbol` / `get_code_file_outline` over full file reads (70-98% token savings).
5. Follow `retrieval_strategy` hints from bootstrap (`task_type`, `preferred_tools`).

### B) During implementation [DIRECT MODE ONLY]

- Follow canonical memory decisions unless user explicitly overrides.
- Memory-heavy ops (extraction, summarization, synthesis) → ALWAYS use local Sub-LM via `llm_query` / `llm_query_many` first. Cloud consumes compact Sub-LM outputs only.
- Memory routing (strict):
  - edit/delete → `propose_memory_mutation(...)` then `apply_memory_mutation(mutation_plan=...operations...)`
  - create/save → append strict `extracted_fact` + `consolidate_memory(...)`
  - Mismatch → block with `OP_RULES_BLOCKED`, never silently fallback.

### C) After implementation [DIRECT MODE ONLY]

Write facts to `memory/logs/extracted_facts.jsonl` — **strict schema**:
```json
{"type":"extracted_fact","ts":"<ISO-8601>","value":{"type":"<rule|task|fix|decision|change|analysis|feature|architecture|api>","entity":"<snake_id>","date":"<YYYY-MM-DD>","value":"<description>","source":"session:<id>","priority":<0-10>,"status":"active"}}
```
Then run `consolidate_memory(project_path=<workspace_root>)`.

## Safety & Autonomy

- Never fabricate memory facts. Mark assumptions explicitly.
- Preserve existing memory files; avoid destructive rewrites.
- Execute memory sync proactively unless user says "skip memory update".
- Keep responses concise and action-oriented.

