# Local Iteration Log Overwrite Policy — 2026-03-02

## META
- id: local_iteration_log_overwrite_20260302
- updated_at: 2026-03-02T03:15:00Z
- source: user request

### Summary
- Added dedicated local-model iteration log file: `memory/logs/local_llm_iterations.log`.
- Log file is overwritten from scratch on every new local model request (`llm_query` or `llm_query_many`).
- For batch requests, each prompt/response pair is recorded as an iteration in that single request log.
