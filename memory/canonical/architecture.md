# Canonical Architecture Memory

## META
- id: architecture
- updated_at: 2026-03-07T22:56:49.986690+01:00
- source: memory/logs/extracted_facts.jsonl
- items: 7

### autopilot_orchestrator_mode_override
- [architecture][active;p=9] Added ORCHESTRATOR MODE OVERRIDE section to copilot-instructions.md. When orchestration is active, Primary Goal, Sections B/B1/B2/C, Autonomy Policy, and Response Style are SUSPENDED. Only HARD GATE, Section A, Safety, and Slash Commands remain active. Slash Commands moved up near HARD GATE for higher LLM attention weight. All suspended sections marked [DIRECT MODE ONLY] with warning blocks. (source: session:autopilot_orchestrator_conflict_fix)

### canonical_seed_from_rlm_memory_external_project
- [feature][active;p=7] Executed seed_canonical_from_rlm_memory.py for external project D:/MCOC/NativeMod/STUDIO.ROJECTS/BNM dobby1/MyApplication; created memory/canonical files from memory/rlm_memory with counts architecture=47, coding_rules=20, active_tasks=11 and seeded_facts=78. (source: session:current_chat)

### canonical_seed_script
- [feature][active;p=10] Added standalone script scripts/seed_canonical_from_rlm_memory.py to extract facts from memory/rlm_memory markdown files, append extracted_facts log, and generate canonical files plus seed changelog without server module dependency. (source: session:canonical_seed_workflow_20260302)

### changelog_retention
- [architecture][active;p=7] Added auto-summarization pipeline for old rlm_consolidation changelogs into monthly summaries with optional archival of raw files. (source: session:auto_summarize_old_changelogs)

### code_index_dependencies
- [architecture][active;p=6] Code index uses tree-sitter>=0.24 with individual language packages (tree-sitter-python, tree-sitter-javascript, etc.) as optional dependencies in pyproject.toml [project.optional-dependencies] code-index group. (source: session:copilot)

### consolidate_memory_tool
- [api][active;p=8] Extended consolidate_memory with summarize_old_changelogs, older_than_days, keep_raw_changelogs, max_files_per_summary. (source: session:consolidate_memory_api_update)

### orchestrator_context_resilience_checkpoint
- [architecture][active;p=9] Added context resilience mechanism to orchestrator: checkpoint file (.vscode/tasks/orchestrator_state.json) written after every state transition, mandatory re-orientation step (re-read checkpoint + master_plan + protocol reminder) before every new task and before closure. Solves context window degradation in long orchestration runs where LLM forgets instructions, skips archivist, and fails to clean .vscode/tasks/. (source: session:context_resilience_fix)
