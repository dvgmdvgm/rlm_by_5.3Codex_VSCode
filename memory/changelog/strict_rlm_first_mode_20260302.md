# Policy Update — Strict RLM-First Mode

## META
- id: strict_rlm_first_mode_20260302
- updated_at: 2026-03-02T01:40:00Z
- source: user clarification

### Rule
- For memory-heavy extraction/summarization/synthesis/classification, use local Sub-LM first (`llm_query`/`llm_query_many`).
- Avoid cloud-side direct summarization of long memory files when Sub-LM extraction is available.
- Cloud model should aggregate decisions using compact Sub-LM outputs.
