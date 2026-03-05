# Canonical Active Tasks Memory

## META
- id: active_tasks
- updated_at: 2026-03-05T16:20:35.322137+01:00
- source: memory/logs/extracted_facts.jsonl
- items: 27

### autopilot_bootstrap_hard_gate
- [fix][active;p=10] Rewrote copilot-instructions.md to fix unreliable memory bootstrap execution: added HARD GATE section at top of file before Primary Goal, removed conditional first-message-only language (now unconditional on every message), added explicit STOP/block directives, converted step 0 to a gate-check reference, made get_memory_metadata optional instead of mandatory, reduced from 8 to 6 pre-implementation steps. (source: session:copilot)

### bootstrap_install
- [task][active;p=6] Added scripts/install_rlm_bootstrap.ps1 to install only reusable integration assets via sparse checkout (excluding server source). (source: session:github_bootstrap_installer)

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

### migrate_legacy_facts_script
- [change][active;p=6] Created scripts/rlm/migrate_legacy_facts.py — one-time migration utility that converts non-canonical JSONL records to strict extracted_fact format. Supports --dry-run. Successfully migrated 21 facts in art_network_antigravity project. (source: session:refactor_scripts_rlm_20260302)

### migrate_legacy_facts_summary_type_guard
- [fix][active;p=8] Fixed scripts/rlm/migrate_legacy_facts.py to safely coerce non-string legacy summary/value payloads before truncation, preventing KeyError during migration. (source: session:legacy_migration_current_and_neighbor_20260303)

### neighbor_project_already_strict_no_migration_needed
- [analysis][active;p=8] Neighbor project d:/art_network_antigravity extracted_facts.jsonl already conforms to strict extracted_fact schema (outer_bad=0, inner_bad=0); no migration writes required. (source: session:legacy_migration_current_and_neighbor_20260303)

### orchestrator_comprehensive_rules_audit_report
- [change][active;p=9] Added mandatory Comprehensive Rules Audit Report to orchestration final output: synthesizer now produces per-task TASK_RULES_AUDIT table covering ALL active rules (applied/skipped/failed with reasons); skill.md accumulates audits across tasks and requires full rules report in final user-facing response; archivist verifies rules audit completeness at closure. (source: session:copilot)

### unknown_session
- [change][active;p=7] {"type": "task", "entity": "Baseline Tasks", "date": "", "value": "Keep memory project-specific and continue canonical consolidation after major sessions.", "source": "memory/changelog/memory_reset_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Planner Artifacts", "date": "2026-03-02", "value": "Created minimal planning artifacts for car-selection 3D rotating visualization request (diagnostic:off): updated .vscode/tasks/master_plan.md and added task_01_ui_selection_contract.md, task_02_3d_viewer_integration.md, task_03_validation_and_handoff.md; planning-only, no code implementation.", "source": "session:planner_car_3d_visualization_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Files", "date": "2026-03-02", "value": "Updated examples/login_page.html for Task 01 only: added selection payload attributes on car buttons, added #carViewerMount container, and wired car:selected dispatch/listener contract.", "source": "session:worker_task_01_ui_selection_contract_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "review", "entity": "Task 01 UI Selection Contract", "date": "2026-03-02", "value": "Reviewer verdict APPROVE: minimal selection contract and explicit #carViewerMount are present in examples/login_page.html; no additional task-01-unrelated UX changes detected in worker scope artifacts.", "source": "session:reviewer_task_01_ui_selection_contract_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Files", "date": "2026-03-02", "value": "Updated examples/login_page.html for Task 02: added CSS 3D scene, rotating car model mock, carId-based visual variants, asset availability check, and live viewer status messaging without backend.", "source": "session:worker_task_02_3d_viewer_integration_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "review", "entity": "Task 02 3D Viewer Integration", "date": "2026-03-02", "value": "Reviewer gate APPROVE confirmed for .vscode/tasks/task_02_3d_viewer_integration.md: selected car display, continuous rotation, selection switch update, and visible missing-model fallback requirements are accepted.", "source": "session:synthesizer_task_02_memory_gate_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Task 03 Validation + Handoff", "date": "2026-03-02", "value": "Validated Task 01/02 acceptance criteria directly in examples/login_page.html and updated .vscode/tasks/master_plan.md with completed statuses and caveat that examples/assets/models/* is absent and viewer uses CSS 3D fallback without real GLB renderer.", "source": "session:worker_task_03_validation_handoff_20260302"} (source: session:unknown_session)
- [review][active;p=7] REJECT for .vscode/tasks/task_03_validation_and_handoff.md: file contains plan template only and does not document actual Task01/Task02 validation evidence or concise handoff caveats; master_plan completion status is updated. (source: session:unknown_session)
- [change][active;p=7] {"type": "review", "entity": "Task 03 Validation + Handoff", "date": "2026-03-02", "value": "Synthesizer memory gate executed after reviewer APPROVE; Task 01 and Task 02 acceptance criteria recorded as PASS with evidence and caveats documented in .vscode/tasks/task_03_validation_and_handoff.md.", "source": "session:synthesizer_task_03_memory_gate_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Archivist Closure Pass", "date": "2026-03-02", "value": "Closure audit for car-selection 3D orchestration run (diagnostic:off): planned tasks in .vscode/tasks/master_plan.md are marked complete and reviewer approvals are present for Task 01/02/03 (Task 03 via re-review).", "source": "session:archivist_closure_pass_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Memory Sync Gate Coverage", "date": "2026-03-02", "value": "Evidence exists for synthesizer memory sync on Task 02 and Task 03; no explicit standalone Task 01 memory-sync gate artifact was found, so strict per-approved-task gate traceability is partially blocked.", "source": "session:archivist_closure_pass_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "review", "entity": "Task 01 Memory Sync Gate", "date": "2026-03-02", "value": "Re-ran memory sync and created explicit gate artifact .vscode/tasks/task_01_memory_sync_gate.md containing required MEMORY_SYNC_OK marker after approved Task 01 outcomes.", "source": "session:synthesizer_task_01_memory_gate_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Archivist Closure Recheck", "date": "2026-03-02", "value": "Post-remediation recheck confirms Task 01/02/03 are complete with approvals present and per-approved-task memory sync evidence available (Task 01 explicit gate file with MEMORY_SYNC_OK; Task 02/03 synthesizer gate evidence in extracted facts). Final closure status: no blockers.", "source": "session:archivist_closure_recheck_post_task01_gate_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Memory Sync Gate Coverage", "date": "2026-03-02", "value": "Task 01 gate remediation completed: per-approved-task evidence now exists for Task 01/02/03 (Task 01 explicit .vscode/tasks/task_01_memory_sync_gate.md with MEMORY_SYNC_OK; Task 02 and Task 03 synthesizer gate evidence recorded in memory/logs/extracted_facts.jsonl). No remaining gate blocker for closure.", "source": "session:archivist_closure_recheck_post_task01_gate_20260302"} (source: session:unknown_session)
