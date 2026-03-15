# Copilot Instructions — RLM Memory Autopilot

## ⛔ HARD GATE — MEMORY BOOTSTRAP (runs FIRST on EVERY message)

Before ANY response: call `local_memory_bootstrap(question=<user_task>, project_path=<workspace_root>)` and WAIT for result.
**No exceptions.** Not for simple questions. Not for follow-ups. Not ever.

**Exception**: If your prompt contains `[ORCHESTRATED_SUBAGENT]`, skip bootstrap entirely. Your context is already provided by the orchestrator.

---

## Slash Commands

- `/orchestrate` (or explicit reference to `orchestrate.prompt.md`): invoke `.github/prompts/orchestrator_skill.prompt.md`, delegate to subagents only. Orchestrator is a state-machine manager — it MUST NOT code directly. When orchestration is active, sections B/C below are SUSPENDED (handled by worker/synthesizer/archivist subagents). If planner delegation fails, return `ORCHESTRATOR_NOT_AVAILABLE` and STOP.

---

## Memory Workflow

### A) Before work (always)

1. Use `brief` from bootstrap as primary context. Respect `user_response_language`.
2. **If `canonical_read_needed` is `false`** in bootstrap → do NOT read canonical files. The brief is sufficient.
3. **If `canonical_read_needed` is `"rules_only"`** → read ONLY `coding_rules.md`. Skip `architecture.md` and `active_tasks.md`.
4. Only if brief is insufficient or contradictory, read all canonical: `architecture.md`, `coding_rules.md`, `active_tasks.md`.
5. When `code_index_summary` present → prefer `search_code_symbols` / `get_code_symbol` / `get_code_file_outline` over full file reads (70-98% token savings).
6. Follow `retrieval_strategy` hints from bootstrap (`task_type`, `preferred_tools`).
7. **If `workflow_hints` present** → follow them strictly. They contain context-saving instructions (subagent decomposition, read/write order, search strategy).

### A.1) Token efficiency rules (always)
- **Read files in 1 large chunk** — never split a 1000-line file into 3 reads of 300.
- **Never re-read** a file already in context. If summarization compresses history, use subagents instead.
- **Backup before create** — `Move-Item .bak` THEN `create_file`. Never reverse.
- **Targeted search** — use 2-3 specific globs, not 10 exploratory patterns.
- **Prefer code_index over grep chains** — `search_code_symbols` (1 call) replaces 3-5 sequential `grep_search` calls for class/function discovery.
- **Rewrite tasks** → decompose into subagents (1 per file type: CSS, templates, JS). Each gets a clean context window, reads + writes without context competition.
- **If `workflow_hints.file_sizes` present** → use the `recommendation` field per file: `"read_full_once"` = read in 1 call, `"use_code_index"` = use `get_code_file_outline` + `get_code_symbol`.
- **Terminal paths** — always wrap paths with spaces in double quotes: `& "path\to\python.exe" -m py_compile "path\to\file.py"`.
- **Orchestration finalization** — use single CLI command instead of 4-5 separate calls: `python -m rlm_mcp.cli.finalize_orchestration --project-root "<path>" --run-id "<run_id>"`.
- **Worker trust** — reviewer verifies via `get_errors`/`py_compile` for small changes (<50 lines). For large changes (>100 lines) re-read only modified sections. For security-critical code or 3rd retry — full re-read mandatory.

### A.2) Terminal command execution (always, Windows/PowerShell)

**MANDATORY**: When you need to execute a shell command and read its output, use `run_compressed_command` MCP tool INSTEAD of `run_in_terminal`. This provides:
1. **Auto-fix of 17 PowerShell syntax errors** — Bash→PS fixes (&&→;, grep→Select-String, rm -rf, export, etc.) applied BEFORE execution. Prevents retry loops.
2. **Auto-resolve Python through venv** — `python`, `pip`, `pytest`, etc. are automatically routed through the project's `.venv` without needing to activate it first. Eliminates 2-3 retry calls.
3. **Incremental timeout guards** — silent commands fail fast with startup/idle/overall timeout metadata instead of hanging the UI for ~60s with no visible output.
4. **Output compression (60-97% token savings)** — git, grep, test, ls outputs are compressed automatically.
5. **Token savings tracking** — every call is logged for analytics (`token_gain` tool).

**When to use which tool:**
| Scenario | Tool |
|---|---|
| Run command + read output | `run_compressed_command` ✅ |
| Long-running/background process (server, watch) | `run_in_terminal` (isBackground=true) |
| Interactive terminal (user types) | `run_in_terminal` |
| Check command syntax without executing | `fix_command` |
| Compress text already in context | `compress_text` |
| View token savings stats | `token_gain` / `token_gain_history` |

**Never** use `run_in_terminal` for read-output commands like `git status`, `git log`, `grep`, `pytest`, `ls`, `dir` when `run_compressed_command` is available.

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

