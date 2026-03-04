# Canonical Active Tasks Memory

## META
- id: active_tasks
- updated_at: 2026-03-04T18:01:57.619546+01:00
- source: memory/logs/extracted_facts.jsonl
- items: 77

### added_configurable_local_timestamp_mode
- [change][active;p=8] Implemented configurable timestamp mode across MCP server, REPL logs, and consolidator with new RLM_TIMESTAMP_MODE (local|utc), defaulting to local time for user-friendly timestamps. (source: session:copilot)

### autopilot_bootstrap_hard_gate
- [fix][active;p=10] Rewrote copilot-instructions.md to fix unreliable memory bootstrap execution: added HARD GATE section at top of file before Primary Goal, removed conditional first-message-only language (now unconditional on every message), added explicit STOP/block directives, converted step 0 to a gate-check reference, made get_memory_metadata optional instead of mandatory, reduced from 8 to 6 pre-implementation steps. (source: session:copilot)

### bootstrap_default_target
- [fix][active;p=9] Installer TargetProjectPath is now optional and defaults to current directory, enabling one-command install from inside target project folder. (source: session:bootstrap_default_current_dir_20260302)

### bootstrap_hidden_dirs_behavior
- [analysis][active;p=7] Confirmed generator includes .md in ALLOWED_SUFFIXES but excludes hidden dirs by default (except .github), so .agent/memory markdowns were skipped unless --include-hidden is used; evidence: default scan 35 files vs include-hidden scan 290 files with .agent dominant. (source: session:current_chat)

### bootstrap_install
- [task][active;p=6] Added scripts/install_rlm_bootstrap.ps1 to install only reusable integration assets via sparse checkout (excluding server source). (source: session:github_bootstrap_installer)

### bootstrap_installer_empty_github_guard
- [fix][active;p=10] Installer now copies directory contents via Copy-Item -Path with wildcard and verifies key files inside .github; empty .github no longer passes verification. (source: session:bootstrap_empty_github_guard_20260302)

### bootstrap_installer_github_copy
- [fix][active;p=10] Fixed scripts/install_rlm_bootstrap.ps1 directory copy logic: removed invalid LiteralPath wildcard copy and now copy container path directly so .github is imported with contents. (source: session:bootstrap_oneliner_github_empty_fix_20260302)

### bootstrap_reliability
- [fix][active;p=10] Installer no longer uses sparse-checkout; switched to shallow clone + direct copy of required paths with strict post-copy verification of .github, .vscode/mcp.json, and generator script. (source: session:bootstrap_shallow_clone_fix_20260302)

### bootstrap_sparse_checkout
- [fix][active;p=9] Installer switched sparse-checkout to --no-cone with rooted paths for single-file imports and now throws immediately on git command failures. (source: session:bootstrap_sparse_checkout_fix_20260302)

### bootstrap_target_path
- [fix][active;p=8] Installer now auto-creates TargetProjectPath when it does not exist; removed hard failure on missing path. (source: session:bootstrap_target_path_autocreate_20260302)

### canonical_seed_from_rlm_memory_external_project
- [feature][active;p=7] Executed seed_canonical_from_rlm_memory.py for external project D:/MCOC/NativeMod/STUDIO.ROJECTS/BNM dobby1/MyApplication; created memory/canonical files from memory/rlm_memory with counts architecture=47, coding_rules=20, active_tasks=11 and seeded_facts=78. (source: session:current_chat)

### classify_fact_two_level_routing
- [fix][active;p=10] Rewrote _classify_fact in consolidator.py: added two-level routing (Level 1: fact.type as primary deterministic signal via type-to-bucket map; Level 2: keyword scan on entity+value only with word-boundary regex). Fixes incorrect routing where type=rule facts with task-like words in value went to active_tasks instead of coding_rules. Changed priority order to rules > tasks > architecture. (source: session:copilot)

### communication_language_parser
- [fix][active;p=9] Language parser now matches only non-comment COMMUNICATION_LANGUAGE lines to avoid false match on descriptive comment text. (source: session:language_parser_comment_fix_20260302)

### current_project_legacy_facts_migrated_to_strict
- [change][active;p=9] Migrated current project memory/logs/extracted_facts.jsonl from mixed legacy/canonical layout to fully strict extracted_fact schema (outer_bad=0, inner_bad=0). (source: session:legacy_migration_current_and_neighbor_20260303)

### dry_run_delete_ui_buttons_rule
- [analysis][active;p=7] Executed proposal-only memory mutation for deleting UI button color rule; mode remained off, apply blocked, mutation_plan generated with 3 deprecate operations targeting matched active facts. (source: session:copilot)

### explained_end_to_end_cloud_local_memory_flow_detailed
- [analysis][active;p=7] Provided detailed end-to-end explanation of cloud-local memory interaction flow, including bootstrap, retrieval, selection, local summarization, execution, consolidation, pitfalls, and fallback paths. (source: session:copilot)

### External Project Memory Repair
- [task][active;p=8] Executed seed_canonical_from_rlm_memory.py for d:/art_network_antigravity and appended OPS-RULE-MOBILE-BUILD-001 in compatible extracted_fact.value format; subsequent consolidation produced non-empty canonical files and promoted rule into canonical/active_tasks.md. (source: session:external_project_seed_and_rule_repair_20260302)

### external_memory_language_audit
- [analysis][active;p=7] Audit of D:/art_network_antigravity/memory found 30 memory files with Cyrillic present in 2 files: rlm_memory/03_decisions/inferred_decisions.md and rlm_memory/07_context/implementation_patterns.md. (source: session:external_memory_audit_20260302)

### external_memory_translation
- [change][active;p=8] Translated Russian snippets to English in D:/art_network_antigravity/memory/rlm_memory/03_decisions/inferred_decisions.md and 07_context/implementation_patterns.md; Cyrillic audit now reports zero files. (source: session:external_memory_translation_20260302)

### external_preferences_payload_test
- [analysis][active;p=9] Direct bootstrap test for D:/art_network_antigravity now returns user_response_language=ru and user_response_style hint from rlm_memory/13_preferences/communication.md; compact payload includes brief (~235 chars), selected_count=8, and aggregate memory_stats. (source: session:language_parser_comment_fix_20260302)

### external_project_fact_migration
- [change][active;p=8] Migrated D:/art_network_antigravity/memory/logs/extracted_facts.jsonl: 204 input lines -> 214 output (193 already canonical, 11 legacy records expanded to 21 canonical facts); subsequent consolidation raised active_tasks from 20 to 33 items. (source: session:strict_fact_schema_20260302)

### external_project_operational_rule_audit
- [analysis][active;p=9] Audited d:/art_network_antigravity: orchestration prompts require operational-rule checks, but run evidence showed RULES_CHECKED=0 while an active mobile build rule existed in memory/logs/extracted_facts.jsonl. Canonical files were empty (items:0), and the run effectively used canonical-only interpretation, causing false-negative rule execution for mobile task. (source: session:external_project_rule_audit_20260302)

### GitHub Push
- [task][active;p=8] Committed and pushed orchestration operational-rules gate updates to main branch with commit a7f20b8. (source: session:push_operational_rules_gate_20260302)
- [task][active;p=8] Pushed workflow hardening changes to main branch with commit 55c197f and prepared operator guidance for manual/automatic memory consolidation triggers. (source: session:push_and_consolidation_guidance_20260302)
- [task][active;p=8] Pushed memory sync after workflow hardening to main branch with commit 038c2a1. (source: session:push_memory_sync_20260302)
- [task][active;p=8] Pushed canonical memory, changelog, and cloud payload logs update to main branch with commit c58abd7. (source: session:push_canonical_and_payload_logs_20260302)

### github_push
- [task][active;p=7] Initialized git repo, created root commit, added origin https://github.com/dvgmdvgm/rlm_by_5.3Codex_VSCode.git, and pushed main successfully. (source: session:git_push_20260302)
- [task][active;p=8] Pushed strict schema migration and memory artifacts to main branch with commit 8c0f667. (source: session:push_strict_migration_20260303)

### hybrid_changelog_trigger_and_logs_audit
- [change][active;p=9] Implemented hybrid changelog autosummarization trigger in src/rlm_mcp/server.py using age OR volume thresholds (file count and bytes). Updated README Consolidation API and retention policy docs. Audited memory/logs outputs for both RLM_Realization and art_network_antigravity projects. (source: session:hybrid_changelog_policy_20260303)

### migrate_legacy_facts_script
- [change][active;p=6] Created scripts/rlm/migrate_legacy_facts.py — one-time migration utility that converts non-canonical JSONL records to strict extracted_fact format. Supports --dry-run. Successfully migrated 21 facts in art_network_antigravity project. (source: session:refactor_scripts_rlm_20260302)

### migrate_legacy_facts_summary_type_guard
- [fix][active;p=8] Fixed scripts/rlm/migrate_legacy_facts.py to safely coerce non-string legacy summary/value payloads before truncation, preventing KeyError during migration. (source: session:legacy_migration_current_and_neighbor_20260303)

### mutation_plan_operations_only_standard
- [decision][active;p=10] Adopted strict single mutation standard: apply_memory_mutation accepts only mutation_plan.operations from propose_memory_mutation and explicitly rejects legacy mutation_plan.facts format. (source: session:copilot)

### neighbor_mobile_rule_migration_and_consolidation
- [change][active;p=9] Executed migration and consolidation in d:/art_network_antigravity: appended strict structured operational payload for OPS-RULE-MOBILE-BUILD-001 and reconsolidated canonical memory. Canonical active_tasks now contains structured OPS-RULE-MOBILE-BUILD-001 payload with rule_id/scope/trigger/action/preconditions/failure_policy/evidence/status/priority. Legacy unknown_session line remains as historical entry. (source: session:neighbor_rule_migration_20260303)

### neighbor_project_already_strict_no_migration_needed
- [analysis][active;p=8] Neighbor project d:/art_network_antigravity extracted_facts.jsonl already conforms to strict extracted_fact schema (outer_bad=0, inner_bad=0); no migration writes required. (source: session:legacy_migration_current_and_neighbor_20260303)

### operational_rule_trigger_diagnosis
- [analysis][active;p=8] In external project chat, OPS-RULE-MOBILE-BUILD-001 existed in extracted_facts log, did not apply to backend-only serializer fix (scope mismatch), and should have applied to later mobile app task but was not triggered because orchestration flow lacks explicit post-task operational-rule execution and canonical memory there remained empty after consolidation. (source: session:rule_trigger_diagnosis_20260302)

### orchestrate_not_triggered_without_slash_prefix
- [analysis][active;p=8] Diagnosed orchestrator bypass: user prompt used "Follow instructions in orchestrate.prompt.md" instead of starting message with exact /orchestrate trigger; session executed standard direct workflow (search/read/edit) rather than planner-worker-reviewer orchestration. (source: session:copilot)

### Orchestration Operational Rules Gate
- [rule][active;p=10] After each approved task, synthesizer must evaluate all active operational rules from project memory, execute matched actions, and return OP_RULES_OK together with MEMORY_SYNC_OK before advancement/cleanup gates. (source: session:orchestration_operational_rules_gate_patch_20260302)

### orchestration_cleanup_policy
- [rule][active;p=9] Delete .vscode/tasks only after all tasks are done, all approved tasks passed MEMORY_SYNC_OK, and archivist returned ARCHIVE_OK; preserve diagnostic audit by copying to memory/logs before cleanup. (source: session:strict_tasks_cleanup_policy_20260302)

### orchestration_operational_rule_hardening
- [change][active;p=10] Hardened operational-rule workflows: save_operational_memory_rule and /save-memory-rule now require structured operational payload with stable rule_id and canonical token verification; synthesizer/orchestrator gate now requires strict OP_RULES_OK criteria with per-matched-rule execution evidence (command, exit_code, output_summary), per-task independent re-evaluation, and OP_RULES_BLOCKED on missing evidence or blocking failures. (source: session:op_rules_hardening_20260303)

### orchestrator_fail_fast_no_silent_fallback
- [fix][active;p=9] Hardened orchestrator activation rules: added explicit trigger alias for orchestrate prompt-file requests and fail-fast ORCHESTRATOR_NOT_AVAILABLE guard when planner delegation does not start, across copilot instructions, orchestrate command, and orchestrator prompts. (source: session:copilot)

### orchestrator_routing_bypass_despite_slash_command
- [analysis][active;p=8] Refined diagnosis: user may have invoked /orchestrate, but session evidence shows direct-agent execution path (no planner-worker-reviewer-synthesizer stage artifacts in chat trace), indicating orchestration routing/delegation did not engage in that run rather than user trigger error. (source: session:copilot)

### project_scoped_mutation_mode_env_fallback
- [fix][active;p=9] Made memory mutation mode project-aware: precedence is process env RLM_MEMORY_MUTATION_MODE, then credentials.env, then .env in project_path root, then default off. (source: session:copilot)

### strict_fact_schema_enforcement
- [fix][active;p=10] Added strict JSON schema for extracted_facts.jsonl to copilot-instructions.md in both RLM server and external project; consolidator only accepts records with type=extracted_fact and nested value dict — all other formats are silently skipped. (source: session:strict_fact_schema_20260302)

### unknown_session
- [change][active;p=7] {"type": "rule", "entity": "RLM MCP Server", "date": "", "value": "Project is a Python MCP server implementing Hybrid RLM memory workflow.", "source": "memory/changelog/memory_reset_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Agentic Workflow", "date": "", "value": "Planner queries RLM first, Worker queries targeted memory before coding, Reviewer enforces APPROVE/REJECT gate.", "source": "memory/changelog/memory_reset_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Baseline Tasks", "date": "", "value": "Keep memory project-specific and continue canonical consolidation after major sessions.", "source": "memory/changelog/memory_reset_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "UI Buttons", "date": "", "value": "Mandatory rule: for future web page layout tasks, all site buttons must be red unless explicitly overridden by the user for that task.", "source": "memory/changelog/button_color_rule_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Orchestrate Invocation", "date": "", "value": "Use .github/prompts/orchestrate.prompt.md as primary entrypoint when /orchestrate is not visible in chat UI.", "source": "memory/changelog/orchestrate_promptfile_fix_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "decision", "entity": "UI Login Page", "date": "", "value": "Implemented a static login page without backend logic containing username/password fields and a submit button.", "source": "session:orchestrate_login_page_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Files", "date": "", "value": "Added examples/login_page.html and orchestration artifacts under .vscode/tasks for planner-worker-reviewer flow.", "source": "session:orchestrate_login_page_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Orchestration Comparison", "date": "", "value": "Legacy setup had explicit orchestrator->planner/worker/reviewer/synthesizer/archivist delegation semantics, while current setup is role-based prompts/skills and lacks dedicated synthesizer+archivist enforcement and strict subagent isolation guarantees.", "source": "memory/changelog/orchestration_comparison_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Strict Orchestration Workflow", "date": "", "value": "State machine is mandatory: Planner -> (Worker<->Reviewer up to 3 attempts) -> Synthesizer after each APPROVE -> Archivist closure; halt and request human intervention on 3rd REJECT.", "source": "memory/changelog/strict_orchestration_state_machine_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Files", "date": "", "value": "Updated examples/login_page.html and orchestration artifacts under .vscode/tasks to reflect strict planner-worker-reviewer-synthesizer-archivist workflow for this session.", "source": "session:orchestrate_auth_carshop_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Files", "date": "", "value": "Updated examples/login_page.html and .vscode/tasks orchestration artifacts for strict planner-worker-reviewer-synthesizer-archivist execution in the theme-toggle session.", "source": "session:orchestrate_theme_toggle_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Communication Style", "date": "", "value": "Primary response template is defined in memory/canonical/communication.md (standard pattern: topic header, analysis/main content, summary/next steps), with structured/scannable formatting preferred.", "source": "session:memory_communication_template_check_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Slash Orchestrate Routing", "date": "", "value": "If prompt starts with /orchestrate, orchestrator must invoke .github/prompts/orchestrator_skill.prompt.md and delegate to subagents instead of doing implementation directly.", "source": "memory/changelog/slash_orchestrator_routing_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Planner Artifacts", "date": "2026-03-02", "value": "Created minimal planning artifacts for car-selection 3D rotating visualization request (diagnostic:off): updated .vscode/tasks/master_plan.md and added task_01_ui_selection_contract.md, task_02_3d_viewer_integration.md, task_03_validation_and_handoff.md; planning-only, no code implementation.", "source": "session:planner_car_3d_visualization_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "decision", "entity": "UI Selection Contract", "date": "2026-03-02", "value": "Implemented minimal car selection contract in examples/login_page.html via document-level event car:selected with payload { carId, modelPath } and no 3D engine initialization.", "source": "session:worker_task_01_ui_selection_contract_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "decision", "entity": "UI 3D Viewer Mount", "date": "2026-03-02", "value": "Defined explicit viewer mount point #carViewerMount in examples/login_page.html that updates placeholder state based on selected car payload.", "source": "session:worker_task_01_ui_selection_contract_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Files", "date": "2026-03-02", "value": "Updated examples/login_page.html for Task 01 only: added selection payload attributes on car buttons, added #carViewerMount container, and wired car:selected dispatch/listener contract.", "source": "session:worker_task_01_ui_selection_contract_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "review", "entity": "Task 01 UI Selection Contract", "date": "2026-03-02", "value": "Reviewer verdict APPROVE: minimal selection contract and explicit #carViewerMount are present in examples/login_page.html; no additional task-01-unrelated UX changes detected in worker scope artifacts.", "source": "session:reviewer_task_01_ui_selection_contract_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "decision", "entity": "UI 3D Viewer Integration", "date": "2026-03-02", "value": "Implemented lightweight CSS 3D rotating car visualization in #carViewerMount with no external dependencies and live variant switching from car:selected payload.", "source": "session:worker_task_02_3d_viewer_integration_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "UI 3D Fallback", "date": "2026-03-02", "value": "If .glb asset is unavailable, UI shows a visible warning fallback note while keeping rotating CSS 3D car preview active.", "source": "session:worker_task_02_3d_viewer_integration_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Files", "date": "2026-03-02", "value": "Updated examples/login_page.html for Task 02: added CSS 3D scene, rotating car model mock, carId-based visual variants, asset availability check, and live viewer status messaging without backend.", "source": "session:worker_task_02_3d_viewer_integration_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "review", "entity": "Task 02 3D Viewer Integration", "date": "2026-03-02", "value": "Reviewer gate APPROVE confirmed for .vscode/tasks/task_02_3d_viewer_integration.md: selected car display, continuous rotation, selection switch update, and visible missing-model fallback requirements are accepted.", "source": "session:synthesizer_task_02_memory_gate_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Task 03 Validation + Handoff", "date": "2026-03-02", "value": "Validated Task 01/02 acceptance criteria directly in examples/login_page.html and updated .vscode/tasks/master_plan.md with completed statuses and caveat that examples/assets/models/* is absent and viewer uses CSS 3D fallback without real GLB renderer.", "source": "session:worker_task_03_validation_handoff_20260302"} (source: session:unknown_session)
- [review][active;p=7] REJECT for .vscode/tasks/task_03_validation_and_handoff.md: file contains plan template only and does not document actual Task01/Task02 validation evidence or concise handoff caveats; master_plan completion status is updated. (source: session:unknown_session)
- [review][active;p=7] APPROVE for .vscode/tasks/task_03_validation_and_handoff.md: includes explicit Task01/Task02 criterion-by-criterion PASS statuses with evidence, concise Handoff/Caveats section, and scoped file-change list for no-git-metadata context. (source: session:unknown_session)
- [change][active;p=7] {"type": "review", "entity": "Task 03 Validation + Handoff", "date": "2026-03-02", "value": "Synthesizer memory gate executed after reviewer APPROVE; Task 01 and Task 02 acceptance criteria recorded as PASS with evidence and caveats documented in .vscode/tasks/task_03_validation_and_handoff.md.", "source": "session:synthesizer_task_03_memory_gate_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Archivist Closure Pass", "date": "2026-03-02", "value": "Closure audit for car-selection 3D orchestration run (diagnostic:off): planned tasks in .vscode/tasks/master_plan.md are marked complete and reviewer approvals are present for Task 01/02/03 (Task 03 via re-review).", "source": "session:archivist_closure_pass_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Memory Sync Gate Coverage", "date": "2026-03-02", "value": "Evidence exists for synthesizer memory sync on Task 02 and Task 03; no explicit standalone Task 01 memory-sync gate artifact was found, so strict per-approved-task gate traceability is partially blocked.", "source": "session:archivist_closure_pass_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "review", "entity": "Task 01 Memory Sync Gate", "date": "2026-03-02", "value": "Re-ran memory sync and created explicit gate artifact .vscode/tasks/task_01_memory_sync_gate.md containing required MEMORY_SYNC_OK marker after approved Task 01 outcomes.", "source": "session:synthesizer_task_01_memory_gate_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Archivist Closure Recheck", "date": "2026-03-02", "value": "Post-remediation recheck confirms Task 01/02/03 are complete with approvals present and per-approved-task memory sync evidence available (Task 01 explicit gate file with MEMORY_SYNC_OK; Task 02/03 synthesizer gate evidence in extracted facts). Final closure status: no blockers.", "source": "session:archivist_closure_recheck_post_task01_gate_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "task", "entity": "Memory Sync Gate Coverage", "date": "2026-03-02", "value": "Task 01 gate remediation completed: per-approved-task evidence now exists for Task 01/02/03 (Task 01 explicit .vscode/tasks/task_01_memory_sync_gate.md with MEMORY_SYNC_OK; Task 02 and Task 03 synthesizer gate evidence recorded in memory/logs/extracted_facts.jsonl). No remaining gate blocker for closure.", "source": "session:archivist_closure_recheck_post_task01_gate_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Global MCP Server Routing", "date": "", "value": "Use fixed server command path with workspace-bound cwd and RLM_MEMORY_DIR (${workspaceFolder}/memory) to keep memory project-local while reusing one global MCP server codebase.", "source": "memory/changelog/global_server_per_project_memory_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] Implemented --emit-json-graph mode in codebase memory generator. (source: session:unknown_session)
- [change][active;p=7] Fixed user response language inference to prioritize chat language directives. (source: session:unknown_session)
