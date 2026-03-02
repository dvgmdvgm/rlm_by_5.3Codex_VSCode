# Canonical Coding Rules Memory

## META
- id: coding_rules
- updated_at: 2026-03-02T12:17:02.554117+00:00
- source: memory/logs/extracted_facts.jsonl
- items: 18

### changelog_retention
- [architecture][active;p=7] Added auto-summarization pipeline for old rlm_consolidation changelogs into monthly summaries with optional archival of raw files. (source: session:auto_summarize_old_changelogs)

### Conflict Resolution Policy
- [rule][active;p=0] Winner order: active status > higher priority > newer timestamp > higher source rank; only active winners are published in canonical memory. (source: memory/changelog/conflict_resolution_policy_20260302.md)

### LLM Trace Visibility
- [rule][active;p=0] execute_repl_code returns llm_trace with truncated prompt/response previews for llm_query and llm_query_many calls; optional persistent JSONL trace is configurable. (source: memory/changelog/llm_trace_visibility_20260302.md)

### Local Iteration Logging
- [rule][active;p=0] Local iteration log file is rewritten on each new llm_query/llm_query_many request and stores only the current request iterations. (source: memory/changelog/local_iteration_log_overwrite_20260302.md)
- [rule][active;p=0] local_llm_iterations.log is overwritten on each new local model request; for batch calls it stores all iterations of the current batch only. (source: memory/changelog/local_iteration_log_overwrite_20260302.md)

### Local LLM Integration
- [rule][active;p=0] Ollama backend is used with default model qwen2.5-coder:14b. (source: memory/changelog/memory_reset_20260302.md)

### Memory Processing Policy
- [rule][active;p=0] Strict RLM-First Mode: memory-heavy extraction/summarization/synthesis must use local Sub-LM first; cloud should consume compact Sub-LM outputs. (source: memory/changelog/strict_rlm_first_mode_20260302.md)

### Memory Workflow
- [rule][active;p=0] Before work: reload memory and read canonical files; after work: append facts and consolidate memory. (source: memory/changelog/memory_reset_20260302.md)

### memory_loading
- [rule][active;p=8] Exclude memory/_archive/* from active memory context and metadata to prevent archival bloat in retrieval. (source: session:memory_store_archive_filter)

### Orchestration Diagnostic Mode
- [rule][active;p=0] Use diagnostic:on for audit proof of role-stage invocations; use diagnostic:off to disable diagnostic logging and avoid extra overhead. (source: memory/changelog/orchestration_diagnostic_mode_20260302.md)

### REPL Runtime
- [rule][active;p=0] Stateful REPL supports memory_context, llm_query, llm_query_many, FINAL and FINAL_VAR. (source: memory/changelog/memory_reset_20260302.md)

### RLM MCP Server
- [rule][active;p=0] MCP transport in MVP is stdio. (source: memory/changelog/memory_reset_20260302.md)

### RLM-First Demonstration
- [rule][active;p=0] Canonical memory extraction demo used llm_query_many with 4 chunk calls and cloud consumed compact aggregated output only. (source: memory/changelog/strict_rlm_first_mode_20260302.md)

### UI Auth + Car Shop Mock
- [decision][active;p=0] Expanded examples/login_page.html to include login, registration, and a static car store section with purchase simulation controls; no backend added. (source: session:orchestrate_auth_carshop_20260302)

### UI Buttons
- [rule][active;p=0] All action buttons in the auth and car-shop mock UI remain red, following the mandatory project button color policy. (source: session:orchestrate_auth_carshop_20260302)
- [rule][active;p=0] All action buttons, including the theme toggle, remain red in both light and dark themes per project policy. (source: session:orchestrate_theme_toggle_20260302)
- [rule][active;p=0] User override applied: in examples/login_page.html light theme button tokens are green; dark theme button tokens remain red. (source: session:orchestrate_light_theme_green_buttons_20260302)

### UI Theme Toggle
- [decision][active;p=0] Added light/dark mode toggle to examples/login_page.html with token-based styling and persisted theme selection in localStorage. (source: session:orchestrate_theme_toggle_20260302)
