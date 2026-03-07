# Copilot Instructions — RLM Memory Autopilot

## ⛔ HARD GATE — MEMORY BOOTSTRAP (runs FIRST on EVERY message)

Before ANY analysis, coding, planning, searching, or substantive response:

1. Resolve `project_path` from the active workspace root.
2. Call `local_memory_bootstrap(question=<user_task>, project_path=<project_path>)`.
3. **WAIT** for the result. Do not proceed until bootstrap returns.

**DO NOT skip this step.** Not for "simple" questions. Not for follow-ups. Not ever.
Allowed pre-bootstrap actions: resolving workspace path and minimal intent parsing ONLY.
If you find yourself about to respond without having called bootstrap — **STOP and call it NOW.**

---

## ⛔ ORCHESTRATOR MODE OVERRIDE

When orchestration is active (triggered by `/orchestrate`, `orchestrate.prompt.md`, or `orchestrator_skill.prompt.md`), the following autopilot sections are **SUSPENDED**:

| Suspended section | Reason | Who handles it instead |
|---|---|---|
| **Primary Goal** ("Execute the requested coding/research work") | Orchestrator MUST NOT code directly — only delegate to subagents | `#agent:worker` |
| **Section B** ("During implementation") | Orchestrator does not implement — workers do | `#agent:worker` |
| **Section B1** ("Strict RLM-First Mode") | Memory-heavy ops are delegated to synthesizer | `#agent:synthesizer` |
| **Section B2** ("Deterministic Memory Routing") | Memory writes routed through synthesizer gate | `#agent:synthesizer` |
| **Section C** ("After implementation") | Memory persistence is synthesizer's job, not orchestrator's | `#agent:synthesizer` |
| **Autonomy Policy** ("Execute memory sync proactively") | Memory sync follows strict gate protocol per task | `#agent:synthesizer` + `#agent:archivist` |
| **Response Style** ("Prefer execution over proposing long plans") | Orchestrator REQUIRES a formal planning phase | `#agent:planner` |

What REMAINS active during orchestration:
- **HARD GATE** — bootstrap still runs first
- **Section A** — memory loading before work (planner uses it)
- **Safety** — always active
- **Slash Commands** — routing logic below

If you are the orchestrator: you are a **state-machine manager**, not a coding agent. Delegate everything. If in doubt, re-read `orchestrator_skill.prompt.md`.

---

## SLASH COMMANDS

- `/orchestrate`: If the user starts a prompt with exactly this word, you MUST immediately invoke the rules defined in `.github/prompts/orchestrator_skill.prompt.md`.
- Equivalent explicit trigger: if user message explicitly asks to follow `.github/prompts/orchestrate.prompt.md` (for example, "Follow instructions in orchestrate.prompt.md"), treat it as `/orchestrate` and route to orchestrator workflow.
- Delegate planning to `#agent:planner` first.
- Do NOT perform planning/implementation/review/synthesis directly as the orchestrator role.
- The orchestrator role is a state-machine manager only.
- Fail-fast guard: if orchestrator activation was requested but planner delegation did not start, STOP and return `ORCHESTRATOR_NOT_AVAILABLE` with concise recovery steps; do not continue in direct execution mode.

---

This workspace uses a Hybrid RLM Memory System. Behave as an autonomous memory-aware coding agent.

## Primary Goal [DIRECT MODE ONLY]

For every user task, automatically:
1. Load and use project memory context before coding.
2. Execute the requested coding/research work.
3. Persist important new decisions/facts into memory.
4. Consolidate memory so canonical files stay up to date.

> ⚠️ **This section applies only in DIRECT mode.** When orchestrator is active, these goals are handled by subagents — see ORCHESTRATOR MODE OVERRIDE above.

## Mandatory Workflow

### A) Before implementation (always)

1. **Bootstrap gate check** — if you have NOT yet called `local_memory_bootstrap` in this turn, STOP everything and call it now (see HARD GATE above). No exceptions.
2. Use `brief` and `selected_files` from bootstrap result as primary memory context.
3. Respect language hints from bootstrap:
   - keep local memory processing English-only,
   - set final user response language using `user_response_language` (or communication canonical rules if `auto`).
4. Optionally call `get_memory_metadata(project_path=<active_workspace_root>, max_files=20, include_headers=false, include_files=false)` for aggregate diagnostics.
5. Read canonical memory only if bootstrap brief is insufficient or contradictory:
   - `memory/canonical/architecture.md`
   - `memory/canonical/coding_rules.md`
   - `memory/canonical/active_tasks.md`
6. Use memory findings to shape implementation choices and avoid regressions.

### A1) Code Index Integration (auto when available)

When bootstrap response includes `code_index_summary`, use code index tools for efficient code context:

1. **Prefer code index tools** over reading full source files:
   - Understanding project structure → `get_code_file_outline(file_path, project_path)`
   - Finding functions/classes/methods → `search_code_symbols(query, project_path=...)`
   - Retrieving implementation of a known symbol → `get_code_symbol(symbol_id, project_path)`
2. **Auto-index trigger**: If bootstrap does NOT include `code_index_summary` and the task requires code understanding, call `index_project_code(project_path=...)` once to build the index.
3. **Token efficiency**: These tools return only needed code fragments via O(1) byte-offset seeking instead of reading entire files (70-98% token savings).
4. **Stale index**: If indexed files were recently modified, re-run `index_project_code` to refresh.

### B) During implementation [DIRECT MODE ONLY]

> ⚠️ **Suspended when orchestrator is active.** Worker agents handle implementation.

- Follow decisions from canonical memory unless user explicitly overrides.
- If memory is stale or missing key info, call `local_memory_bootstrap(question=..., project_path=<active_workspace_root>)` first.
- If still insufficient, call `local_memory_brief(question=..., project_path=<active_workspace_root>)` with larger `max_files`/`max_chars_per_file`.
- If still insufficient, extract facts via REPL (`execute_repl_code(..., project_path=...)` + `llm_query` / `llm_query_many`) from relevant memory files only.
- Keep prompts to local model strict and extraction-focused.

### B1) Strict RLM-First Mode (default) [DIRECT MODE ONLY]

> ⚠️ **Suspended when orchestrator is active.** Synthesizer handles memory operations.

- For memory-heavy operations (fact extraction, summarization, synthesis, classification), ALWAYS use local Sub-LM via `llm_query` / `llm_query_many`.
- Do NOT summarize large memory files directly in cloud context if Sub-LM can do it first.
- Cloud model should aggregate/decide using compact outputs produced by Sub-LM.
- Direct deterministic writes without Sub-LM are allowed only for:
   - explicit user one-line rules (e.g., "save this exact rule")
   - mechanical metadata updates (timestamps, status fields)
   - final file write operations after Sub-LM extraction is complete

### B2) Deterministic Memory Routing Policy (strict) [DIRECT MODE ONLY]

> ⚠️ **Suspended when orchestrator is active.** Synthesizer handles memory routing.

- Classify memory intent before write path selection:
   - `edit/delete existing memory facts` -> MUST use mutation pipeline only:
      1) `propose_memory_mutation(...)`
      2) `apply_memory_mutation(mutation_plan=...operations...)`
   - `create/save new rule/fact` -> MUST use direct strict `extracted_fact` append + immediate `consolidate_memory(...)`.
- For mutation apply, only `mutation_plan.operations` is valid; legacy `mutation_plan.facts` is invalid.
- Any path-policy mismatch must return/emit blocked status (`OP_RULES_BLOCKED` or equivalent gate block) and MUST NOT silently fallback to another write path.

### C) After implementation [DIRECT MODE ONLY]

> ⚠️ **Suspended when orchestrator is active.** Synthesizer persists memory; archivist verifies at closure.

1. Write a compact session memory entry to `memory/logs/extracted_facts.jsonl` with key outcomes:
   - architectural decisions
   - API changes
   - constraints and caveats
   - file-level changes

   **STRICT FORMAT — every JSONL line MUST follow this exact schema:**
   ```json
   {"type": "extracted_fact", "ts": "<ISO-8601 UTC>", "value": {"type": "<rule|task|fix|decision|change|analysis|feature|review|architecture|api>", "entity": "<short_snake_case_id>", "date": "<YYYY-MM-DD>", "value": "<concise human-readable description>", "source": "session:<session_id>", "priority": <0-10>, "status": "active"}}
   ```
   - `type` (outer): MUST be exactly `"extracted_fact"` — no other values.
   - `value` (outer): MUST be a JSON object with all fields above — no flat/alternative layouts.
   - Any record that does not match this schema will be silently skipped by the consolidator and NEVER appear in canonical memory.
   - Do NOT invent alternative formats (e.g. `{"type": "feature", ...}` or `{"session": ..., "facts": [...]}`).
2. Run `consolidate_memory(project_path=<active_workspace_root>)`.
   - If consolidation requires semantic grouping from large logs, perform grouping prompts through Sub-LM first, then write canonical files.
3. In final answer, include:
   - what was changed
   - which memory artifacts were updated
   - any follow-up actions

## Autonomy Policy

- Do not ask the user to manually run memory tools for routine tasks.
- Execute memory sync/consolidation proactively unless user says "skip memory update".
- If a memory operation fails, attempt one fallback strategy and report concise status.

## Response Style

- Keep responses concise and action-oriented.
- Prefer execution over proposing long plans.
- Treat this memory system as first-class project infrastructure.

## Safety

- Never fabricate memory facts.
- Mark uncertain inferences as assumptions.
- Preserve existing memory files; avoid destructive rewrites outside canonical/changelog outputs.

