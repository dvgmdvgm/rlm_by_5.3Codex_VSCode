# Hybrid RLM Memory MCP Server

MCP server on Python for a stateful REPL workflow with local LLM querying.

## Features

- Stateful Python REPL tool: `execute_repl_code(code: str, project_path: str | None = None)`
- Local model query from REPL globals: `llm_query(prompt)`
- Finalization helpers: `FINAL(text)` and `FINAL_VAR(var_name)`
- Preloaded in-memory context: `memory_context`
- Memory metadata tool: `get_memory_metadata(project_path: str | None = None)`
- Local memory synthesis tool: `local_memory_brief(question: str, project_path: str | None = None, ...)`
- Local-first bootstrap tool: `local_memory_bootstrap(question: str, project_path: str | None = None, ...)`
- Memory reload tool: `reload_memory_context(project_path: str | None = None)`
- Canonical memory consolidation tool: `consolidate_memory(..., project_path: str | None = None)`

## Quick start

1. Install dependencies:

```bash
pip install -e .
```

2. Optional env vars:

- `RLM_MEMORY_DIR` (default: `memory`)
- `RLM_OLLAMA_URL` (default: `http://127.0.0.1:11434`)
- `RLM_OLLAMA_MODEL` (default: `qwen2.5-coder:14b`)
- `RLM_OLLAMA_TIMEOUT` (default: `120`)
- `RLM_MAX_CONCURRENCY` (default: `6`)
- `RLM_TRACE_PREVIEW_CHARS` (default: `280`)
- `RLM_TRACE_PERSIST` (default: `false`)
- `RLM_TRACE_FILE` (default: `memory/logs/llm_trace.jsonl`)
- `RLM_LOCAL_ITER_LOG_ENABLED` (default: `true`)
- `RLM_LOCAL_ITER_LOG_FILE` (default: `memory/logs/local_llm_iterations.log`)
- `RLM_LOCAL_ITER_LOG_PREVIEW_CHARS` (default: `420`)
- `RLM_LOCAL_LLM_FORCE_ENGLISH` (default: `true`)

3. Run server (stdio):

```bash
python -m rlm_mcp.server
```

## REPL globals

Inside `execute_repl_code`, these globals are available:

- `memory_context: dict[str, str]`
- `llm_query(prompt: str) -> str`
- `llm_query_many(prompts: list[str], max_concurrency: int | None = None) -> list[str]`
- `FINAL(text: str) -> None`
- `FINAL_VAR(var_name: str) -> None`

`execute_repl_code` response includes `llm_trace` with per-call previews from local model interactions:

- `call_type`, `ok`, `prompt_chars`, `response_chars`
- `prompt_preview`, `response_preview`
- batch metadata for `llm_query_many`

If `RLM_TRACE_PERSIST=true`, all trace events are also appended to `memory/logs/llm_trace.jsonl`.

Local iteration log behavior:

- Runtime writes local-model iteration events to `RLM_LOCAL_ITER_LOG_FILE`.
- The file is overwritten from scratch on each new `llm_query` or `llm_query_many` request.
- For `llm_query_many`, each prompt/response pair is logged as an iteration in the current request file.

## Consolidation API

`consolidate_memory(`
`log_rel_path: str = "logs/extracted_facts.jsonl",`
`write_changelog: bool = True,`
`refresh_context: bool = True,`
`project_path: str | None = None,`
`summarize_old_changelogs: bool = True,`
`older_than_days: int = 2,`
`keep_raw_changelogs: bool = False,`
`max_files_per_summary: int = 20`
`) -> dict`

Returns counters and output file paths:

- `total_log_records`, `extracted_fact_records`, `unique_facts`
- `architecture_items`, `coding_rules_items`, `active_tasks_items`
- `architecture_path`, `coding_rules_path`, `active_tasks_path`, `changelog_path`
- `reloaded_files` (if `refresh_context=True`)
- `summaries_created`, `raw_files_summarized`, `raw_files_archived` (if summarization enabled)

Auto-summarization policy:

- Old `memory/changelog/rlm_consolidation_*.md` files are summarized by the **local model**.
- Raw old files are archived to `memory/_archive/changelog_raw/` by default (`keep_raw_changelogs=false`).
- Archived files are excluded from active memory loading.

## Compact metadata mode

`get_memory_metadata` now defaults to compact output to reduce cloud token usage:

- `max_files=20`
- `include_headers=false`
- `include_files=false`
- `sort_by="chars_desc"`

Additional aggregate fields are returned even in compact mode:

- `total_files`, `total_chars`, `total_lines`, `truncated`

For cheapest checks, call with:

- `include_files=false` (aggregates only, no file list)

## Local-first brief (recommended)

Use `local_memory_brief(question, project_path=...)` to push retrieval + synthesis to local model and send only a compact brief to cloud model.

Language policy:

- Local model output is English-only by default (`RLM_LOCAL_LLM_FORCE_ENGLISH=true`).
- Cloud/user response language should follow memory communication preferences.

For one-call bootstrap, use `local_memory_bootstrap(question, project_path=...)`.

Typical flow:

1. `local_memory_bootstrap(question="...", project_path="<active_workspace_root>")`
2. Cloud model consumes only `brief`, `selected_files`, and lightweight `memory_stats`
3. Only if needed, call deeper tools (`local_memory_brief` with larger limits or `execute_repl_code`)

`local_memory_bootstrap` also returns language hints:

- `local_model_output_language` (expected local model language)
- `user_response_language` (inferred from memory preferences)

Conflict resolution policy during consolidation:

- Rules with same `conflict_key` are resolved deterministically.
- Winner selection order: `status(active > deprecated)` -> `priority(higher wins)` -> `timestamp(newer wins)` -> `source_rank(session > changelog > memory)`.
- Only active winners are published into canonical files.

## Memory format

See `memory/README.md` and `prompts/system_prompt_root.md`.

## Practical REPL template

- End-to-end chunking + parallel extraction example:
	- `examples/repl_recursive_workflow.md`

## MCP client configs

- VS Code workspace config: `.vscode/mcp.json`
- Claude Desktop example: `examples/claude_desktop_mcp_config.json`

Global server + per-project memory model (recommended):

- Keep `command` fixed to this repository's Python environment (global MCP server location).
- Keep `cwd` fixed to this repository path.
- Pass `project_path` in every memory-sensitive tool call from the active workspace root.

This allows one global MCP server codebase to be reused across projects while each active project keeps its own isolated `memory/` files.

Quick verification after connecting the MCP server:

1. Call `get_memory_metadata(project_path="<active_workspace_root>")`
2. Call `execute_repl_code(..., project_path="<active_workspace_root>")` with:

```repl
print(list(memory_context.keys())[:3])
FINAL("ok")
```

## Copilot Autopilot Mode

This workspace includes `.github/copilot-instructions.md`.

- Copilot auto-loads memory context before task execution.
- Copilot auto-updates memory logs and runs `consolidate_memory()` after task execution.
- To opt out for one request, include phrase: `skip memory update`.

## Orchestrate invocation

- Preferred: use prompt file `.github/prompts/orchestrate.prompt.md` from Copilot prompt picker.
- If `/orchestrate` is not visible in chat UI, reload VS Code window/new chat session.
- Note: `.github/commands/orchestrate.md` is a project convention file; slash command visibility depends on client capabilities/extensions.

## Minimal bootstrap import command

Use this one-liner to import the minimal downstream set from GitHub:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([ScriptBlock]::Create((Invoke-WebRequest 'https://raw.githubusercontent.com/dvgmdvgm/rlm_by_5.3Codex_VSCode/main/scripts/install_rlm_bootstrap.ps1' -UseBasicParsing).Content))"
```

Imported by default:

- `.github/`
- `.vscode/mcp.json`
- `scripts/generate_rlm_memory_from_code.py`

If `TargetProjectPath` does not exist, installer creates it automatically.
Optional: pass `-TargetProjectPath "D:/your/project"` to install into a different folder.

Without `ps1`, use native git import flow from `docs/github-bootstrap-install.md` (section: `Native git mode`).

## Local guide and rollback

- Local guide for this feature: `docs/local-first-memory-guide.md`
- Full single-file project briefing for new context windows: `docs/context-window-briefing.md`
- Codebase bootstrap workflow (generate RLM memory from raw code): `docs/codebase-to-rlm-memory-workflow.md`
- GitHub bootstrap install guide: `docs/github-bootstrap-install.md`
- Generator script: `scripts/generate_rlm_memory_from_code.py`
- One-command bootstrap installer for other projects: `scripts/install_rlm_bootstrap.ps1`
- Minimal downstream import set: `.github/`, `.vscode/mcp.json`, and `scripts/generate_rlm_memory_from_code.py`
- Optional graph export: run generator with `--emit-json-graph` to produce `code_graph.json`
- Chat prompt workflow: `.github/prompts/bootstrap_memory_from_codebase.prompt.md`
- Chat command workflow: `.github/commands/bootstrap-memory.md`
- Backup snapshot (pre-local-first): `backups/pre_local_first_20260302/`
- One-step rollback script: `backups/pre_local_first_20260302/restore.ps1`

## Documentation handoff checklist

For sharing full project context with developers and cloud models, provide these files first:

- `docs/context-window-briefing.md`
- `.github/copilot-instructions.md`
- `README.md`
- `docs/local-first-memory-guide.md`
- `docs/codebase-to-rlm-memory-workflow.md`
