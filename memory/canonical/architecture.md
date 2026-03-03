# Canonical Architecture Memory

## META
- id: architecture
- updated_at: 2026-03-03T16:51:52.006400+01:00
- source: memory/logs/extracted_facts.jsonl
- items: 3

### canonical_seed_script
- [feature][active;p=10] Added standalone script scripts/seed_canonical_from_rlm_memory.py to extract facts from memory/rlm_memory markdown files, append extracted_facts log, and generate canonical files plus seed changelog without server module dependency. (source: session:canonical_seed_workflow_20260302)

### consolidate_memory_tool
- [api][active;p=8] Extended consolidate_memory with summarize_old_changelogs, older_than_days, keep_raw_changelogs, max_files_per_summary. (source: session:consolidate_memory_api_update)

### memory_mutation_documentation_refresh
- [change][active;p=9] Expanded documentation for feature-flagged memory mutation: README now includes API contract, mode guards, semantics, safety guarantees and examples; docs/context-window-briefing.md updated with mutation tool contract, env var, status snapshot and risk mitigation; docs/local-first-memory-guide.md updated with safe mutation workflow and usage examples. (source: session:memory_mutation_docs_refresh_20260302)
