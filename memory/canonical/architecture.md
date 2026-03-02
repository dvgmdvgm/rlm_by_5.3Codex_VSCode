# Canonical Architecture Memory

## META
- id: architecture
- updated_at: 2026-03-02T17:55:54.851779+00:00
- source: memory/logs/extracted_facts.jsonl
- items: 2

### canonical_seed_script
- [feature][active;p=10] Added standalone script scripts/seed_canonical_from_rlm_memory.py to extract facts from memory/rlm_memory markdown files, append extracted_facts log, and generate canonical files plus seed changelog without server module dependency. (source: session:canonical_seed_workflow_20260302)

### consolidate_memory_tool
- [api][active;p=8] Extended consolidate_memory with summarize_old_changelogs, older_than_days, keep_raw_changelogs, max_files_per_summary. (source: session:consolidate_memory_api_update)
