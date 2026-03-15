# Canonical Active Tasks Memory

## META
- id: active_tasks
- updated_at: 2026-03-14T22:46:16.503302+01:00
- source: memory/logs/extracted_facts.jsonl
- items: 9

### bootstrap_install
- [task][active;p=6] Added scripts/install_rlm_bootstrap.ps1 to install only reusable integration assets via sparse checkout (excluding server source). (source: session:github_bootstrap_installer)

### copilot_bridge_pending_e2e_test
- [task][active;p=8] Pending: end-to-end test of Agent Mode. Need to verify: relay running, extension auto-connects, phone sends prompt, LLM triggers tool calls (e.g. file_tree), tool_call/tool_result render on phone, final answer displays correctly. (source: session:bridge_memory_save)

### External Project Memory Repair
- [task][active;p=8] Executed seed_canonical_from_rlm_memory.py for d:/art_network_antigravity and appended OPS-RULE-MOBILE-BUILD-001 in compatible extracted_fact.value format; subsequent consolidation produced non-empty canonical files and promoted rule into canonical/active_tasks.md. (source: session:external_project_seed_and_rule_repair_20260302)

### GitHub Push
- [task][active;p=8] Committed and pushed orchestration operational-rules gate updates to main branch with commit a7f20b8. (source: session:push_operational_rules_gate_20260302)
- [task][active;p=8] Pushed workflow hardening changes to main branch with commit 55c197f and prepared operator guidance for manual/automatic memory consolidation triggers. (source: session:push_and_consolidation_guidance_20260302)
- [task][active;p=8] Pushed memory sync after workflow hardening to main branch with commit 038c2a1. (source: session:push_memory_sync_20260302)
- [task][active;p=8] Pushed canonical memory, changelog, and cloud payload logs update to main branch with commit c58abd7. (source: session:push_canonical_and_payload_logs_20260302)

### github_push
- [task][active;p=7] Initialized git repo, created root commit, added origin https://github.com/dvgmdvgm/rlm_by_5.3Codex_VSCode.git, and pushed main successfully. (source: session:git_push_20260302)
- [task][active;p=8] Pushed strict schema migration and memory artifacts to main branch with commit 8c0f667. (source: session:push_strict_migration_20260303)
