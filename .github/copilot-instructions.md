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

#### File reads
- **Read files in 1 large chunk** — never split a 1000-line file into 3 reads of 300.
- **Never re-read** a file already in context. If summarization compresses history, use subagents instead.
- **Plan reads upfront** — before starting, list ALL files you'll need. For each file, identify ALL needed ranges and combine them into 1-2 large reads. Example: if you need lines 100-200 and 300-400 from the same file → read lines 100-400 in one call.
- **Max 2 reads per file per task** — if you've read a file twice and need more, use `get_code_file_outline` to pinpoint exact ranges, then do 1 final read.
- **Parallel reads** — when you need context from multiple independent files, read them in a single parallel batch, not sequentially.
- **Backup before create** — `Move-Item .bak` THEN `create_file`. Never reverse.

#### Search / grep
- **Targeted search** — use 2-3 specific globs, not 10 exploratory patterns.
- **Prefer code_index over grep chains** — `search_code_symbols` (1 call) replaces 3-5 sequential `grep_search` calls for class/function discovery.
- **Consolidate grep per file** — when searching multiple patterns in the same file/scope, combine into ONE `grep_search` with `|` regex alternation. Never search the same file more than twice.
- **Max grep budget** — aim for ≤8 `grep_search` calls per task. If you're exceeding this, you're not combining patterns effectively. Batch related patterns: `class_name|function_name|import_path` in one call.

#### Terminal / validation
- **Terminal paths** — always wrap paths with spaces in double quotes: `& "path\to\python.exe" -m py_compile "path\to\file.py"`.
- **Batch validation** — combine all syntax checks into 1-2 `smart_exec` calls. Example: `python -m py_compile file1.py; python -m py_compile file2.py; node --check file.js` in ONE command, not 3 separate calls.
- **Terminal retry limit** — if a command fails due to shell syntax, use `fix_command` ONCE then retry. Max 2 attempts per command. Never try 4+ variants of the same command.
- **Use `smart_exec` for validation** — all py_compile, node --check, pytest, eslint commands should go through `smart_exec` for compressed output.

#### Orchestration / subagents
- **Rewrite tasks** → decompose into subagents (1 per file type: CSS, templates, JS). Each gets a clean context window, reads + writes without context competition.
- **If `workflow_hints.file_sizes` present** → use the `recommendation` field per file: `"read_full_once"` = read in 1 call, `"use_code_index"` = use `get_code_file_outline` + `get_code_symbol`.
- **Orchestration finalization** — use single CLI command instead of 4-5 separate calls: `python -m rlm_mcp.cli.finalize_orchestration --project-root "<path>" --run-id "<run_id>"`.
- **Worker trust** — reviewer verifies via `get_errors`/`py_compile` for small changes (<50 lines). For large changes (>100 lines) re-read only modified sections. For security-critical code or 3rd retry — full re-read mandatory.

### A.2) Terminal command execution (always, Windows/PowerShell)

**MANDATORY**: Compression tools were removed from the system. Use `fix_command` to normalize Bash-like commands for PowerShell before execution when needed, and use `run_in_terminal` for command execution/output.

**When to use which tool:**
| Scenario | Tool |
|---|---|
| Run command + read output | `run_in_terminal` |
| Run command + **compressed** output (saves 60-90% tokens) | `smart_exec` |
| Long-running/background process (server, watch) | `run_in_terminal` (isBackground=true) |
| Interactive terminal (user types) | `run_in_terminal` |
| Check command syntax without executing | `fix_command` |

**Prefer `smart_exec`** for: git, gh, cargo/npm/go test, pytest, eslint/tsc/ruff/clippy, ls/cat/grep/find, docker/kubectl, pip/pnpm, curl/wget. It auto-detects the command type and compresses output.

**If a command may contain Bash syntax on Windows**, run `fix_command` first, then execute the corrected command with `run_in_terminal`.

### B) During implementation [DIRECT MODE ONLY]

Follow canonical memory decisions unless user explicitly overrides.

#### B.0) Disambiguation (lightweight)
Before coding, assess task clarity. If scope, behavior, or impact is ambiguous:
- Ask 2-3 targeted questions with suggested defaults so the user can confirm quickly.
- Skip if task is trivial, self-explanatory, or user gave explicit instructions.
- Do NOT block — if confidence is high, state your assumptions and proceed.

#### B.1) Test awareness (before writing code)
- If modifying existing code → find and run existing tests for touched files BEFORE making changes. Run them again AFTER.
- If creating new logic (function, class, module) → write at least 1-2 contract tests covering the core behavior. Tests come BEFORE or ALONGSIDE the implementation, not after.
- If task is docs/config/memory-only → skip testing.
- Never delete or weaken existing passing tests to make new code work.

#### B.2) Implement
- Write code following canonical rules from memory.
- Memory-heavy ops (extraction, summarization, synthesis) → ALWAYS use local Sub-LM via `llm_query` / `llm_query_many` first. Cloud consumes compact Sub-LM outputs only.
- Memory routing (strict):
  - edit/delete → `propose_memory_mutation(...)` then `apply_memory_mutation(mutation_plan=...operations...)`
  - create/save → append strict `extracted_fact` + `consolidate_memory(...)`
  - Mismatch → block with `OP_RULES_BLOCKED`, never silently fallback.

#### B.3) Self-review (before responding to user)
Before presenting your solution, internally answer these three questions:
1. **Meaning**: Does this change solve the user's ACTUAL problem? Can I explain it in 2 sentences without referencing implementation details?
2. **Simplicity**: Is there a simpler way using existing project code/utils? Did I introduce unnecessary abstractions?
3. **User impact**: Does this break anything for the end user? Are there silent behavior changes not covered by tests?

If any answer is concerning → fix the issue before responding. Do not present flawed code and hope the user catches it.

#### B.4) Dedup check (after implementation)
- Scan new code for duplicated logic against existing project utilities (`search_code_symbols`).
- If near-duplicate found (>5 lines similar) → refactor to reuse existing code.
- Remove dead code, unused imports, and debug artifacts introduced during this session.
- Skip if change is <10 lines or config/docs only.

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

