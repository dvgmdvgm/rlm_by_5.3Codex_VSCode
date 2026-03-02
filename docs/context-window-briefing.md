# RLM Memory System — Context Window Briefing (Single-File Handoff)

## 1) Purpose of this file

This document is a **single structured handoff source** for starting work in a new chat/context window without losing project continuity.

Use it when:
- a new cloud model session starts,
- context from previous chat windows is unavailable,
- you need to continue implementation with minimal warm-up.

Primary objective:
- preserve seamless development of this memory system across context resets.

---

## 2) Project identity (what this system is)

Project: **Hybrid RLM Memory MCP Server**.

Core idea:
- a Python MCP server that provides persistent, project-bound memory for coding agents.
- memory is read, summarized, and consolidated through a local-first pipeline.
- cloud model should consume compact outputs, not raw large memory files.

Current transport/runtime baseline:
- MCP transport: `stdio`
- Local LLM backend: Ollama
- Default local model: `qwen2.5-coder:14b`
- Local model processing language: English-only by default (`RLM_LOCAL_LLM_FORCE_ENGLISH=true`)

---

## 3) High-level architecture

### 3.1 Runtime shape

- One global server codebase.
- Memory isolation is per project via `project_path`.
- Effective memory directory is resolved as: `<project_path>/memory`.

### 3.2 Main components

- `src/rlm_mcp/server.py`
  - MCP tools (entrypoints)
  - project-path routing
  - per-memory-dir caches for `MemoryStore` and `ReplRuntime`

- `src/rlm_mcp/memory_store.py`
  - recursive load of `.md/.txt/.json/.jsonl`
  - metadata extraction (size/lines/headers)
  - decode fallback support

- `src/rlm_mcp/repl_runtime.py`
  - stateful Python REPL
  - REPL globals: `memory_context`, `llm_query`, `llm_query_many`, `FINAL`, `FINAL_VAR`
  - execution trace support (`llm_trace`)
  - local iteration log behavior (overwrite per request)

- `src/rlm_mcp/llm_adapter.py`
  - local Ollama querying (single + batch async)

- `src/rlm_mcp/consolidator.py`
  - log-to-canonical consolidation
  - deterministic conflict resolution

- `src/rlm_mcp/config.py`
  - environment-configured runtime settings

---

## 4) MCP tools (current operational contract)

### 4.1 Core tools

- `execute_repl_code(code, project_path=None)`
  - executes Python in stateful runtime
  - returns stdout/stderr/error/final/llm_trace

- `get_memory_metadata(project_path=None, max_files=20, include_headers=False, include_files=False, sort_by="chars_desc")`
  - lightweight memory diagnostics
  - defaults are intentionally token-cheap

- `reload_memory_context(project_path=None)`
  - refreshes runtime `memory_context`

- `consolidate_memory(log_rel_path="logs/extracted_facts.jsonl", write_changelog=True, refresh_context=True, project_path=None)`
  - compacts extracted facts into canonical memory and changelog

### 4.2 Local-first tools

- `local_memory_brief(question, project_path=None, max_files=8, max_chars_per_file=3500)`
  - retrieves relevant memory snippets
  - synthesizes compact answer with local model
  - returns `brief` + `selected_files`

- `local_memory_bootstrap(question, project_path=None, max_files=8, max_chars_per_file=3500)`
  - one-call local-first bootstrap:
    1. reload context
    2. aggregate metadata (without heavy file list)
    3. local brief synthesis
  - returns compact packet for cloud model consumption
  - also returns language hints:
    - `local_model_output_language`
    - `user_response_language`

---

## 5) Memory model and file layout

Expected memory root (per project):
- `memory/canonical/`
  - `architecture.md`
  - `coding_rules.md`
  - `active_tasks.md`
  - `communication.md`
- `memory/logs/`
  - `extracted_facts.jsonl`
  - optional trace logs
- `memory/changelog/`
  - consolidation snapshots / historical decisions

### 5.1 Canonical semantics

- `architecture.md`: stable architecture facts
- `coding_rules.md`: durable rules/constraints
- `active_tasks.md`: active task state and key decisions
- `communication.md`: response/formatting behavior profile

### 5.2 Conflict resolution policy

When conflicting facts share conflict-key, winner order is deterministic:
1. active status over deprecated
2. higher priority
3. newer timestamp
4. higher source rank (`session > changelog > memory`)

Only active winners are published in canonical output.

---

## 6) Required operating mode (RLM-first)

### 6.1 Why

Goals:
- reduce cloud token usage,
- reduce context-window drift,
- improve repeatability across sessions.

### 6.2 Rule

For memory-heavy operations (extract/summarize/synthesize/classify):
- local Sub-LM first,
- cloud model aggregates compact local outputs.

Cloud should avoid directly ingesting large memory files unless strictly needed.

### 6.3 Language split rule

- Local Sub-LM memory processing is English-only.
- Cloud model response language for user chat follows `user_response_language` from bootstrap (or canonical communication rules when `auto`).

---

## 7) New context-window start protocol (authoritative)

When a new cloud chat starts, do this sequence:

1. Resolve active workspace root as `project_path`.
2. Call `local_memory_bootstrap(question=<short user task>, project_path=<workspace>)`.
3. Use returned `brief` and `selected_files` as primary context.
4. Respect language hints:
  - local processing context stays English-only,
  - final user response follows `user_response_language`.
5. Call `get_memory_metadata(..., include_files=false)` for aggregate diagnostics only.
6. Read canonical files directly **only if** bootstrap output is insufficient or contradictory.
7. Implement changes.
8. Append compact session fact to `memory/logs/extracted_facts.jsonl`.
9. Run `consolidate_memory(project_path=<workspace>)`.

This is the baseline for seamless cross-window continuity.

---

## 8) Orchestration policy (when using orchestrator flow)

State machine expectation:
- Planner → Worker ↔ Reviewer (max 3 retries) → Synthesizer (memory gate) → Archivist (closure).

Hard rule:
- no advancement to next task before memory sync gate succeeds (`MEMORY_SYNC_OK`) for approved work.

Entrypoint behavior:
- `/orchestrate` routes to orchestrator skill prompt policy.
- prompt-file fallback exists for environments where slash command is not exposed.

---

## 9) Current project status snapshot

- Server supports project-bound memory routing via `project_path`.
- Local-first bootstrap path exists and is documented.
- Metadata defaults are token-cheap (`include_files=false` by default).
- Backup/rollback assets for local-first feature exist.
- Canonical memory consolidation pipeline is operational.

Note:
- canonical architecture file may be sparse at times (depends on extracted fact quality), while coding rules and active tasks are richer.

---

## 10) Files a new model should inspect first (in this order)

1. `.github/copilot-instructions.md`
2. `docs/context-window-briefing.md` (this file)
3. `README.md`
4. `src/rlm_mcp/server.py`
5. `memory/canonical/coding_rules.md`
6. `memory/canonical/active_tasks.md`
7. `memory/canonical/architecture.md`

Only then inspect deep changelog/history if needed.

---

## 11) Practical commands and envs

### 11.1 Run server

- `python -m rlm_mcp.server`

### 11.2 Key env variables

- `RLM_MEMORY_DIR`
- `RLM_OLLAMA_URL`
- `RLM_OLLAMA_MODEL`
- `RLM_OLLAMA_TIMEOUT`
- `RLM_MAX_CONCURRENCY`
- `RLM_TRACE_PERSIST`
- `RLM_TRACE_FILE`
- `RLM_LOCAL_ITER_LOG_ENABLED`
- `RLM_LOCAL_ITER_LOG_FILE`
- `RLM_LOCAL_LLM_FORCE_ENGLISH`

### 11.3 Codebase bootstrap generator

- Script: `scripts/generate_rlm_memory_from_code.py`
- Optional graph export for deeper local reasoning: `--emit-json-graph` (outputs `code_graph.json`)

---

## 12) Known risks and mitigations

### Risk A: Cloud token spikes

Cause:
- reading many large memory files directly in cloud context.

Mitigation:
- always bootstrap locally first,
- keep metadata aggregate-only by default,
- escalate to raw reads only when required.

### Risk B: Memory drift between projects

Cause:
- missing/incorrect `project_path`.

Mitigation:
- pass `project_path` to all memory-sensitive tools,
- verify returned `memory_dir` in tool response.

### Risk C: Noisy/contradictory rules

Cause:
- unstructured logs or conflicting facts.

Mitigation:
- keep extracted facts compact and explicit,
- run consolidation regularly,
- rely on deterministic conflict policy.

---

## 13) Rollback and recovery

If local-first changes need rollback:
- backup snapshot: `backups/pre_local_first_20260302/`
- restore script: `backups/pre_local_first_20260302/restore.ps1`

After restore:
- restart MCP server,
- validate tool behavior against expected baseline.

---

## 14) Definition of done for any future session

A session is complete only when:
1. requested implementation is done,
2. verification is done (errors/tests/smoke where applicable),
3. memory log entry appended,
4. consolidation executed,
5. final response reports changes + memory artifacts.

---

## 15) TL;DR for a brand-new model instance

- This is a Python MCP memory server with project-scoped memory via `project_path`.
- Use `local_memory_bootstrap` first in new context windows.
- Keep cloud context compact; let local model do memory-heavy synthesis.
- Follow orchestration gate discipline if using orchestrator workflow.
- Always persist facts and consolidate memory before closing the task.
