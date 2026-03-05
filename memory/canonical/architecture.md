# Canonical Architecture Memory

## META
- id: architecture
- updated_at: 2026-03-05T16:20:35.321135+01:00
- source: memory/logs/extracted_facts.jsonl
- items: 4

### canonical_seed_from_rlm_memory_external_project
- [feature][active;p=7] Executed seed_canonical_from_rlm_memory.py for external project D:/MCOC/NativeMod/STUDIO.ROJECTS/BNM dobby1/MyApplication; created memory/canonical files from memory/rlm_memory with counts architecture=47, coding_rules=20, active_tasks=11 and seeded_facts=78. (source: session:current_chat)

### canonical_seed_script
- [feature][active;p=10] Added standalone script scripts/seed_canonical_from_rlm_memory.py to extract facts from memory/rlm_memory markdown files, append extracted_facts log, and generate canonical files plus seed changelog without server module dependency. (source: session:canonical_seed_workflow_20260302)

### changelog_retention
- [architecture][active;p=7] Added auto-summarization pipeline for old rlm_consolidation changelogs into monthly summaries with optional archival of raw files. (source: session:auto_summarize_old_changelogs)

### consolidate_memory_tool
- [api][active;p=8] Extended consolidate_memory with summarize_old_changelogs, older_than_days, keep_raw_changelogs, max_files_per_summary. (source: session:consolidate_memory_api_update)
