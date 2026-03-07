# Canonical Coding Rules Memory

## META
- id: coding_rules
- updated_at: 2026-03-07T22:56:49.986690+01:00
- source: memory/logs/extracted_facts.jsonl
- items: 154

### added_configurable_local_timestamp_mode
- [change][active;p=8] Implemented configurable timestamp mode across MCP server, REPL logs, and consolidator with new RLM_TIMESTAMP_MODE (local|utc), defaulting to local time for user-friendly timestamps. (source: session:copilot)

### added_explicit_language_rules_to_neighbor_canonical
- [change][active;p=8] Added explicit language policy rules to D:\art_network_antigravity extracted facts and reconsolidated; confirmed communication_language_policy and local_memory_english_processing appear in canonical/coding_rules.md. (source: session:copilot)

### audited_and_enabled_memory_mutation_for_external_project
- [analysis][active;p=8] Performed mutation audit for D:\art_network_antigravity: validated extracted_facts schema, confirmed apply blocked in mode off, ran isolated ON-mode smoke test of apply pipeline, enabled RLM_MEMORY_MUTATION_MODE=on in external .env with backup, and verified consolidation succeeds. (source: session:copilot)

### audited_external_memory_capacity_and_scaling_risk
- [analysis][active;p=8] Audited D:\art_network_antigravity memory footprint and scaling behavior: current effective memory context is small and fast, logs are largest on disk but excluded from load, changelog auto-summarization thresholds are present, and long-term risk is growth of non-ignored rlm_memory/changelog files. (source: session:copilot)

### bootstrap_command_in_readme
- [decision][active;p=7] README now contains explicit one-liner minimal bootstrap import command from GitHub raw installer. (source: session:readme_minimal_import_command_20260302)

### bootstrap_default_target
- [fix][active;p=9] Installer TargetProjectPath is now optional and defaults to current directory, enabling one-command install from inside target project folder. (source: session:bootstrap_default_current_dir_20260302)

### bootstrap_hidden_dirs_behavior
- [analysis][active;p=7] Confirmed generator includes .md in ALLOWED_SUFFIXES but excludes hidden dirs by default (except .github), so .agent/memory markdowns were skipped unless --include-hidden is used; evidence: default scan 35 files vs include-hidden scan 290 files with .agent dominant. (source: session:current_chat)

### bootstrap_import_set
- [decision][active;p=8] Bootstrap installer imports .github, .vscode/mcp.json, and scripts/generate_rlm_memory_from_code.py for downstream projects. (source: session:bootstrap_include_generator_script_20260302)
- [change][active;p=9] Installer and native git bootstrap docs now import scripts/seed_canonical_from_rlm_memory.py in addition to generate_rlm_memory_from_code.py. (source: session:canonical_seed_workflow_20260302)

### bootstrap_installer_empty_github_guard
- [fix][active;p=10] Installer now copies directory contents via Copy-Item -Path with wildcard and verifies key files inside .github; empty .github no longer passes verification. (source: session:bootstrap_empty_github_guard_20260302)

### bootstrap_installer_github_copy
- [fix][active;p=10] Fixed scripts/install_rlm_bootstrap.ps1 directory copy logic: removed invalid LiteralPath wildcard copy and now copy container path directly so .github is imported with contents. (source: session:bootstrap_oneliner_github_empty_fix_20260302)

### bootstrap_minimal_import
- [decision][active;p=8] Bootstrap installer now imports only .github and .vscode/mcp.json into target projects; docs updated to mark this as minimal recommended set. (source: session:bootstrap_minimal_set_20260302)

### bootstrap_native_git_mode
- [decision][active;p=8] Added native git-only bootstrap flow (without ps1) using fetch + checkout of .github, .vscode/mcp.json, and generator script from remote branch. (source: session:bootstrap_native_git_docs_20260302)

### bootstrap_reliability
- [fix][active;p=10] Installer no longer uses sparse-checkout; switched to shallow clone + direct copy of required paths with strict post-copy verification of .github, .vscode/mcp.json, and generator script. (source: session:bootstrap_shallow_clone_fix_20260302)

### bootstrap_sparse_checkout
- [fix][active;p=9] Installer switched sparse-checkout to --no-cone with rooted paths for single-file imports and now throws immediately on git command failures. (source: session:bootstrap_sparse_checkout_fix_20260302)

### bootstrap_target_path
- [fix][active;p=8] Installer now auto-creates TargetProjectPath when it does not exist; removed hard failure on missing path. (source: session:bootstrap_target_path_autocreate_20260302)

### bootstrap_workflow_chain
- [change][active;p=9] Updated bootstrap-memory prompt/command/docs to run two-step chain: generate_rlm_memory_from_code.py then seed_canonical_from_rlm_memory.py. (source: session:canonical_seed_workflow_20260302)

### briefing_and_readme_op_rules_strictness_alignment
- [documentation][active;p=9] Aligned README and docs/context-window-briefing.md with latest operational-rule hardening: strict OP_RULES_OK criteria, required evidence fields (command/exit_code/output_summary), RULES_FAILED_* and RULES_EVIDENCE_COMPLETE diagnostics, and structured operational payload guidance including rule_id verification in canonical outputs. (source: session:docs_alignment_op_rules_20260303)

### briefing_cloud_payload_and_consolidation_signature_sync
- [documentation][active;p=9] Updated docs/context-window-briefing.md to reflect current consolidate_memory signature (including hybrid changelog triggers) and explicit logs policy: cloud_payload_audit.md append-only, cloud_payload_current.md overwrite snapshot. (source: session:briefing_logs_policy_sync_20260303)

### classify_fact_two_level_routing
- [fix][active;p=10] Rewrote _classify_fact in consolidator.py: added two-level routing (Level 1: fact.type as primary deterministic signal via type-to-bucket map; Level 2: keyword scan on entity+value only with word-boundary regex). Fixes incorrect routing where type=rule facts with task-like words in value went to active_tasks instead of coding_rules. Changed priority order to rules > tasks > architecture. (source: session:copilot)

### cloud_payload_audit_auto_archive
- [feature][active;p=8] Added automatic archival for memory/logs/cloud_payload_audit.md when it reaches 20000 lines by default. Archived audit files are moved into memory/_archive/logs/cloud_payload_audit/, and the threshold can be configured with RLM_CLOUD_PAYLOAD_AUDIT_MAX_LINES or disabled with RLM_CLOUD_PAYLOAD_AUDIT_AUTO_ARCHIVE=false. (source: session:cloud_payload_audit_auto_archive_20260307)

### cloud_payload_audit_generation
- [rule][active;p=10] Cloud payload audit entries are generated by deterministic local Python code in MCP server handlers and do not call local or cloud LLM for log formatting. (source: session:cloud_payload_audit_markdown_20260302)

### cloud_payload_audit_log
- [feature][active;p=10] Server now writes memory/logs/cloud_payload_audit.jsonl on major MCP tool responses with payload chars, estimated tokens, keys, and compact preview of data returned to cloud model. (source: session:cloud_payload_audit_logging_20260302)

### cloud_payload_audit_readable
- [feature][active;p=10] Cloud payload audit log format changed from JSONL to human-readable markdown blocks at memory/logs/cloud_payload_audit.md. (source: session:cloud_payload_audit_markdown_20260302)

### cloud_payload_current_snapshot
- [feature][active;p=10] Added memory/logs/cloud_payload_current.md as single overwrite snapshot file updated on each cloud-facing MCP payload. (source: session:single_file_overwrite_logs_20260302)
- [feature][active;p=10] cloud payload context now always overwrites memory/logs/cloud_payload_current.md as a single latest snapshot (source: session:single_file_overwrite_logs)

### cloud_payload_scope
- [analysis][active;p=9] In bootstrap-first flow cloud receives compact brief + selected file paths + stats, not full code_graph.json; full graph reaches cloud only if explicitly read/requested. (source: session:external_preferences_flow_check_20260302)

### code_graph_handling
- [rule][active;p=9] Large code_graph.json should stay in local memory pipeline; cloud model should consume only filtered/chunked summaries unless explicitly requested. (source: session:external_memory_translation_20260302)

### code_graph_size
- [analysis][active;p=8] D:/art_network_antigravity/memory/rlm_memory/code_graph.json has 10869 lines; this is normal for medium-large codebases and should be kept out of direct cloud prompts unless chunked/summarized. (source: session:external_memory_audit_20260302)

### code_index_bootstrap_integration
- [feature][active;p=8] local_memory_bootstrap now auto-attaches code_index_summary (compact file map + symbol counts) when memory/code_index/index.json exists. Adds ~200 tokens overhead. Copilot-instructions A1 section auto-routes LLM to use code index tools when summary is present. (source: session:copilot)

### code_index_mcp_tools
- [feature][active;p=8] Added 4 new MCP tools: index_project_code, search_code_symbols, get_code_symbol, get_code_file_outline. Each tool response includes token_savings estimate comparing index retrieval vs full file reading. (source: session:copilot)

### code_index_module
- [feature][active;p=8] Added multi-language code indexer (code_index.py) using tree-sitter AST parsing with O(1) byte-offset symbol retrieval. Supports 12 grammars: Python, JS, TS, TSX, CSS, Go, Rust, Java, C#, C, C++, Ruby. Falls back to Python ast when tree-sitter unavailable. (source: session:copilot)

### code_index_token_savings_benchmark
- [analysis][active;p=7] Token savings benchmark on RLM project (16 files, 188 symbols, ~46K tokens): average 93.1% savings across 5 scenarios. Finding a function: 98.6% savings. Getting specific symbol: 71-95% savings. Full outline vs file read: 69.6% savings. (source: session:copilot)

### communication_language_parser
- [fix][active;p=9] Language parser now matches only non-comment COMMUNICATION_LANGUAGE lines to avoid false match on descriptive comment text. (source: session:language_parser_comment_fix_20260302)

### Context Window Briefing
- [documentation][active;p=8] Updated docs/context-window-briefing.md to include operational-rules gate requirements (OP_RULES_OK), synthesizer rule-check diagnostics, minimal operational-rule contract fields, and additional risks for command safety and legacy format compatibility. (source: session:update_context_window_briefing_20260302)

### context_and_memory_readiness_check
- [analysis][active;p=7] Loaded context-window briefing and project memory via local_memory_bootstrap; memory metadata diagnostics confirm accessible project-scoped memory and readiness to continue. (source: session:copilot)

### current_project_legacy_facts_migrated_to_strict
- [change][active;p=9] Migrated current project memory/logs/extracted_facts.jsonl from mixed legacy/canonical layout to fully strict extracted_fact schema (outer_bad=0, inner_bad=0). (source: session:legacy_migration_current_and_neighbor_20260303)

### deprecated_neighbor_language_md_facts_and_reconsolidated
- [change][active;p=8] For D:\art_network_antigravity, deprecated active extracted facts sourced from rlm_memory/13_preferences/language.md after file removal, then ran consolidate_memory and verified canonical no longer references language.md source entries. (source: session:copilot)

### deterministic_memory_routing_and_first_message_bootstrap
- [decision][active;p=10] Updated autopilot/orchestrator/synthesizer/skill prompts to enforce first-message new-context bootstrap guard and strict memory-intent routing: edit/delete uses propose->apply with operations only; create/save uses strict append+consolidate; route mismatch must block with OP_RULES_BLOCKED. (source: session:copilot)

### docs_add_first_message_guard_and_deterministic_routing
- [documentation][active;p=9] Updated README.md, README.ru.md, and docs/context-window-briefing.md to document first-message bootstrap requirement in new context windows and deterministic memory-intent routing policy (edit/delete via propose->apply operations-only; create/save via strict append+consolidate). (source: session:copilot)

### docs_clarify_save_rule_vs_mutation_flows
- [documentation][active;p=8] Updated README.md, README.ru.md, and docs/context-window-briefing.md to explicitly separate operational-rule save flow (append strict extracted_fact + consolidate) from mutation API flow, and to state operations-only apply contract with legacy facts rejection. (source: session:copilot)

### dry_run_delete_ui_buttons_rule
- [analysis][active;p=7] Executed proposal-only memory mutation for deleting UI button color rule; mode remained off, apply blocked, mutation_plan generated with 3 deprecate operations targeting matched active facts. (source: session:copilot)

### enforce_english_local_memory_question_normalization
- [change][active;p=8] Updated local memory tools to normalize non-ASCII user questions into English before retrieval/prompting when RLM_LOCAL_LLM_FORCE_ENGLISH is enabled; added question_en and question_translated in local_memory_brief/bootstrap responses. (source: session:copilot)

### explained_automation_from_rlm_memory_to_canonical
- [analysis][active;p=7] Explained how to automate propagation from rlm_memory to persistent canonical memory using generate->seed->consolidate flow and noted existing Copilot autopilot behavior for extracted facts plus consolidation. (source: session:copilot)

### explained_deeper_tools_usage_rule
- [analysis][active;p=6] Clarified README rule that deeper tools should be called only when bootstrap context is insufficient; described when to use local_memory_brief with larger limits vs execute_repl_code for targeted extraction/validation. (source: session:copilot)

### explained_end_to_end_cloud_local_memory_flow_detailed
- [analysis][active;p=7] Provided detailed end-to-end explanation of cloud-local memory interaction flow, including bootstrap, retrieval, selection, local summarization, execution, consolidation, pitfalls, and fallback paths. (source: session:copilot)

### explained_memory_mutation_purpose_and_off_mode
- [analysis][active;p=7] Analyzed chat history and server behavior: apply_memory_mutation is intended to persist validated mutation operations and auto-consolidate memory, but in user external project it was blocked by mutation mode off, leading to manual fallback writes to extracted_facts.jsonl. (source: session:copilot)

### explained_rlm_memory_vs_canonical_usage_for_external_project
- [analysis][active;p=7] Explained distinction and operational usage for external project memory folders: rlm_memory as generated detailed source context, canonical as consolidated working memory, with guidance to update via extracted_facts plus consolidation rather than manual canonical edits. (source: session:copilot)

### external_bootstrap_flow_validation
- [analysis][active;p=8] Validated local_memory_bootstrap on D:/art_network_antigravity: selected_files included rlm_memory/13_preferences/communication.md and language.md; brief carried style/language summary while user_response_language remained auto due canonical-only inference logic. (source: session:external_preferences_flow_check_20260302)

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

### git_push_state_main_ec56dea
- [analysis][active;p=6] Verified repository push state: local HEAD equals origin/main at ec56dea (ahead/behind 0/0). Working tree has uncommitted changes, so only committed version is pushed. (source: session:copilot)

### gitignore_env_file
- [change][active;p=7] Added .env to .gitignore so local environment file is excluded from git status and accidental commits. (source: session:copilot)

### gitignore_messages_prompts_and_push
- [change][active;p=8] Added messages.md and prompts/ to .gitignore, untracked previously tracked messages.md and prompts files via git rm --cached, committed as c90df3a and pushed to origin/main. (source: session:copilot)

### hybrid_changelog_trigger_and_logs_audit
- [change][active;p=9] Implemented hybrid changelog autosummarization trigger in src/rlm_mcp/server.py using age OR volume thresholds (file count and bytes). Updated README Consolidation API and retention policy docs. Audited memory/logs outputs for both RLM_Realization and art_network_antigravity projects. (source: session:hybrid_changelog_policy_20260303)

### hybrid_post_orchestration_validator
- [feature][active;p=8] Implemented hybrid post-orchestration validator: deterministic Python script (scripts/rlm/validate_orchestrator_rules.py) cross-references orchestrator_state.json + coding_rules.md to find missed operational rules, outputs validation_report.json. Lightweight LLM agent (.github/agents/validator.md) executes only missed rules with minimal context. Phase 4 (Validation) added to skill.md between archivist closure and final cleanup. Updated orchestrator_skill.prompt.md, orchestrate.prompt.md, README.md, context-window-briefing.md. Synced to art_network_antigravity. (source: session:hybrid_validator_implementation)

### identified_neighbor_memory_scripts_and_recommended_fact_workflow
- [analysis][active;p=7] Verified neighbor project has generate_rlm_memory_from_code.py, seed_canonical_from_rlm_memory.py, and write_orchestrator_memory_checklist.py. Recommended workflow: append/update extracted facts for incremental decisions, regenerate rlm_memory only after major codebase shifts, then consolidate canonical. (source: session:copilot)

### local_only_log_generation
- [rule][active;p=10] cloud_payload_current.md and orchestrator_memory_checklist.md are generated by deterministic local code only; no cloud or local LLM calls are used for log formatting. (source: session:single_file_overwrite_logs_20260302)
- [rule][active;p=10] snapshot log files are generated by deterministic local code only (no cloud formatting path) (source: session:single_file_overwrite_logs)

### mcp_json_removed_from_installer
- [change][active;p=7] Removed .vscode/mcp.json from bootstrap installer copy list (install_rlm_bootstrap.ps1) to prevent downstream projects from receiving server-specific MCP config. (source: session:refactor_scripts_rlm_20260302)

### memory_deletion_logic_explained
- [analysis][active;p=7] Explained memory deletion principle: use propose_memory_mutation first, then apply_memory_mutation only in on mode; delete is represented as deprecated extracted_fact plus consolidation-driven canonical update; stressed project_path checks and narrow queries. (source: session:copilot)

### memory_loading
- [rule][active;p=8] Exclude memory/_archive/* from active memory context and metadata to prevent archival bloat in retrieval. (source: session:memory_store_archive_filter)

### memory_loading_noise_control
- [rule][active;p=10] memory/logs/* and memory/_archive/* are excluded from active MemoryStore context/metadata to reduce retrieval noise; logs remain on disk for audit and consolidation workflows. (source: session:exclude_logs_from_context_20260302)

### memory_mutation_documentation_refresh
- [change][active;p=9] Expanded documentation for feature-flagged memory mutation: README now includes API contract, mode guards, semantics, safety guarantees and examples; docs/context-window-briefing.md updated with mutation tool contract, env var, status snapshot and risk mitigation; docs/local-first-memory-guide.md updated with safe mutation workflow and usage examples. (source: session:memory_mutation_docs_refresh_20260302)

### memory_mutation_maintenance_checklist
- [documentation][active;p=9] Added docs/memory-mutation-maintenance-checklist.md with operator-safe procedure for pre-check, mode selection (off/dry-run/on), proposal review, apply verification, post-check and session closure; linked checklist from README local guide section. (source: session:memory_mutation_checklist_20260302)

### memory_mutation_tools_feature_flag
- [change][active;p=9] Added feature-flagged memory mutation workflow with RLM_MEMORY_MUTATION_MODE (off|dry-run|on) and MCP tools propose_memory_mutation/apply_memory_mutation. Existing read/save flows remain unchanged when mode is off. (source: session:memory_mutation_feature_flag_20260302)

### migrate_legacy_facts_script
- [feature][active;p=9] Created scripts/migrate_legacy_facts.py to one-time convert non-canonical JSONL records (flat layouts, wrong outer type, session-facts arrays) into strict extracted_fact format; supports --dry-run preview. (source: session:strict_fact_schema_20260302)

### mutation_mode_global_on
- [decision][active;p=8] Memory mutation mode is now globally hardcoded to 'on' in _effective_mutation_mode() (server.py) and config.py default. ENV variable RLM_MEMORY_MUTATION_MODE is no longer read; all MCP clients get mutation enabled. (source: session:copilot_2026-03-04)

### mutation_plan_operations_only_standard
- [decision][active;p=10] Adopted strict single mutation standard: apply_memory_mutation accepts only mutation_plan.operations from propose_memory_mutation and explicitly rejects legacy mutation_plan.facts format. (source: session:copilot)

### neighbor_mobile_rule_migration_and_consolidation
- [change][active;p=9] Executed migration and consolidation in d:/art_network_antigravity: appended strict structured operational payload for OPS-RULE-MOBILE-BUILD-001 and reconsolidated canonical memory. Canonical active_tasks now contains structured OPS-RULE-MOBILE-BUILD-001 payload with rule_id/scope/trigger/action/preconditions/failure_policy/evidence/status/priority. Legacy unknown_session line remains as historical entry. (source: session:neighbor_rule_migration_20260303)

### neighbor_project_canonical_and_synthesis_format_audit
- [change][active;p=9] Audited d:/art_network_antigravity canonical memory and synthesis contracts. Canonical markdown structure is valid (meta and item-line patterns). Updated neighboring .github synthesizer/orchestrator/save-rule markdown contracts to strict operational-rule format and strict OP_RULES_OK evidence requirements for future canonical-safe synthesis. (source: session:neighbor_project_format_audit_20260303)

### neighbor_project_rlm_memory_report
- [analysis][active;p=6] Reviewed generated memory/rlm_memory in external project D:/MCOC/NativeMod/STUDIO.ROJECTS/BNM dobby1/MyApplication; found 13 category docs plus manifest, 35 scanned files, mostly inferred bootstrap summaries with no detected frameworks/dependencies/tests and dominant markdown-heavy scan composition. (source: session:current_chat)

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

### orchestrator_anti_batching_enforcement
- [rule][active;p=10] Added CRITICAL anti-batching enforcement to skill.md: NO batch execution/review, mandatory per-task synthesizer gate with SYNTHESIZER_GATE_PASSED token, mandatory archivist at closure, self-check before final answer. Added mandatory output format to synthesizer.md with labeled gate block. Synced to art_network_antigravity. Root cause: LLM collapsed state machine into flat batch execution skipping synthesizer/archivist/rules audit entirely. (source: session:copilot)

### orchestrator_fail_fast_no_silent_fallback
- [fix][active;p=9] Hardened orchestrator activation rules: added explicit trigger alias for orchestrate prompt-file requests and fail-fast ORCHESTRATOR_NOT_AVAILABLE guard when planner delegation does not start, across copilot instructions, orchestrate command, and orchestrator prompts. (source: session:copilot)

### orchestrator_memory_checklist_overwrite
- [feature][active;p=10] Added deterministic local script scripts/write_orchestrator_memory_checklist.py and integrated into orchestrator closure flow to overwrite memory/logs/orchestrator_memory_checklist.md on each run. (source: session:single_file_overwrite_logs_20260302)
- [feature][active;p=10] orchestrator closure now writes memory/logs/orchestrator_memory_checklist.md as single overwrite snapshot via scripts/write_orchestrator_memory_checklist.py (source: session:single_file_overwrite_logs)

### orchestrator_routing_bypass_despite_slash_command
- [analysis][active;p=8] Refined diagnosis: user may have invoked /orchestrate, but session evidence shows direct-agent execution path (no planner-worker-reviewer-synthesizer stage artifacts in chat trace), indicating orchestration routing/delegation did not engage in that run rather than user trigger error. (source: session:copilot)

### planner_applied_rules_section
- [feature][active;p=9] Added mandatory Applied Rules section to planner task file template in .github/agents/planner.md. Each task file must now list every canonical memory rule that influenced the plan, with entity name, source file, and one-line summary. Quality bar updated to enforce explicit rule citation. (source: session:copilot)

### project_purpose_summary
- [analysis][active;p=7] Project is a Python MCP server and workflow for Hybrid RLM memory: local-first memory bootstrap/synthesis, stateful REPL tools, canonical memory consolidation, and per-project memory isolation with global server reuse. (source: session:project_about_summary_20260302)

### project_scoped_mutation_mode_env_fallback
- [fix][active;p=9] Made memory mutation mode project-aware: precedence is process env RLM_MEMORY_MUTATION_MODE, then credentials.env, then .env in project_path root, then default off. (source: session:copilot)

### provided_chat_templates_for_memory_deletion
- [analysis][active;p=6] Provided end-user chat templates for safe memory deletion flow: proposal-only, confirm apply, and narrow entity-targeted deletion prompts. (source: session:copilot)

### pushed_orchestrator_failfast_and_ru_readme
- [change][active;p=8] Pushed commit 40f977b to origin/main after rebase; includes orchestrator fail-fast no-silent-fallback rules and Russian README file README.ru.md. (source: session:copilot)

### ran_neighbor_project_consolidation_20260303_120523
- [change][active;p=7] Executed consolidate_memory for D:\art_network_antigravity; canonical files refreshed and changelog rlm_consolidation_20260303_120523.md created. (source: session:copilot)

### readiness_memory_and_briefing_review
- [analysis][active;p=7] Reviewed provided context-window briefing markdown and current project memory via local_memory_bootstrap; confirmed readiness to continue work in this project context. (source: session:copilot)

### readme_logs_quick_triage_cheatsheet
- [documentation][active;p=8] Added Logs quick triage section to README with first-check guidance for extracted facts visibility, cloud payload mismatch, local LLM iterations, orchestration closure status, and rule execution diagnostics fields. (source: session:readme_logs_cheatsheet_20260303)

### readme_russian_version_added
- [feature][active;p=7] Added Russian project documentation file README.ru.md based on README.md structure and current RLM tool contracts. (source: session:copilot)

### rerun_generator_after_agent_rename
- [change][active;p=6] Re-ran generate_rlm_memory_from_code.py as-is for external project after renaming .agent to agent; default scan now includes agent folder and increased scanned files from 35 to 92. (source: session:current_chat)

### Save Memory Rule Workflow
- [rule][active;p=9] Strengthened save-memory-rule workflow to require immediate consolidate_memory and mandatory canonical verification of RULE_ID/fingerprint; workflow must return RULE_SAVED=no with BLOCKED: CANONICAL_PROMOTION_FAILED when promotion is missing. (source: session:save_memory_rule_workflow_hardening_20260302)

### save_memory_rule_command
- [feature][active;p=9] Added command workflow .github/commands/save-memory-rule.md for slash-style invocation of short-request-to-strict-rule memory persistence. (source: session:memory_rule_workflow_20260302)

### save_operational_memory_rule_workflow
- [feature][active;p=10] Added prompt workflow .github/prompts/save_operational_memory_rule.prompt.md to transform short user requests into strict operational memory rules and persist them via extracted_facts + consolidation. (source: session:memory_rule_workflow_20260302)

### schema_recheck_canonical_vs_log_20260303
- [analysis][active;p=8] Rechecked schema integrity: canonical files are structurally valid (META + normalized item lines), and strict save/orchestration workflow contracts remain enforced in .github prompts/commands/agents. extracted_facts.jsonl still contains historical legacy entries (missing priority/status or non-extracted_fact outer layout) from early session lines; consolidator remains tolerant and continues canonical publication from valid extracted_fact records. (source: session:schema_recheck_20260303)

### scripts_moved_to_rlm_subdir
- [change][active;p=8] Moved all scripts from scripts/ to scripts/rlm/ subdirectory. Updated all references across docs, README, .github commands/prompts/skills, and installer in both RLM and downstream (art_network_antigravity) projects. (source: session:refactor_scripts_rlm_20260302)

### snapshot_generator_external_run
- [change][active;p=5] Executed scripts/rlm/generate_rlm_memory_from_code.py as-is for external project root D:/MCOC/NativeMod/STUDIO.ROJECTS/BNM dobby1/MyApplication; generation succeeded and wrote memory/rlm_memory with scanned files summary output. (source: session:current_chat)

### split_cloud_payload_audit_vs_current_formats
- [change][active;p=8] Updated _log_cloud_payload: cloud_payload_audit remains compact (payload_preview), cloud_payload_current now stores full untruncated payload (payload_full). Runtime needs MCP server restart to take effect. (source: session:copilot)

### strict_fact_schema_enforcement
- [fix][active;p=10] Added strict JSON schema for extracted_facts.jsonl to copilot-instructions.md in both RLM server and external project; consolidator only accepts records with type=extracted_fact and nested value dict — all other formats are silently skipped. (source: session:strict_fact_schema_20260302)

### unknown_session
- [change][active;p=7] {"type": "rule", "entity": "RLM MCP Server", "date": "", "value": "Project is a Python MCP server implementing Hybrid RLM memory workflow.", "source": "memory/changelog/memory_reset_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "RLM MCP Server", "date": "", "value": "MCP transport in MVP is stdio.", "source": "memory/changelog/memory_reset_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "REPL Runtime", "date": "", "value": "Stateful REPL supports memory_context, llm_query, llm_query_many, FINAL and FINAL_VAR.", "source": "memory/changelog/memory_reset_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Local LLM Integration", "date": "", "value": "Ollama backend is used with default model qwen2.5-coder:14b.", "source": "memory/changelog/memory_reset_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Memory Workflow", "date": "", "value": "Before work: reload memory and read canonical files; after work: append facts and consolidate memory.", "source": "memory/changelog/memory_reset_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Agentic Workflow", "date": "", "value": "Planner queries RLM first, Worker queries targeted memory before coding, Reviewer enforces APPROVE/REJECT gate.", "source": "memory/changelog/memory_reset_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "UI Buttons", "date": "", "value": "Mandatory rule: for future web page layout tasks, all site buttons must be red unless explicitly overridden by the user for that task.", "source": "memory/changelog/button_color_rule_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "UI Buttons", "date": "", "value": "All website buttons must use red color by default; this is a mandatory UI coding rule unless explicitly overridden by the user.", "source": "memory/changelog/button_color_rule_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Memory Processing Policy", "date": "", "value": "Strict RLM-First Mode: memory-heavy extraction/summarization/synthesis must use local Sub-LM first; cloud should consume compact Sub-LM outputs.", "source": "memory/changelog/strict_rlm_first_mode_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "RLM-First Demonstration", "date": "", "value": "Canonical memory extraction demo used llm_query_many with 4 chunk calls and cloud consumed compact aggregated output only.", "source": "memory/changelog/strict_rlm_first_mode_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Orchestrate Invocation", "date": "", "value": "Use .github/prompts/orchestrate.prompt.md as primary entrypoint when /orchestrate is not visible in chat UI.", "source": "memory/changelog/orchestrate_promptfile_fix_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "decision", "entity": "UI Login Page", "date": "", "value": "Implemented a static login page without backend logic containing username/password fields and a submit button.", "source": "session:orchestrate_login_page_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "UI Buttons", "date": "", "value": "The login page submit button is red, matching project default button color rule.", "source": "session:orchestrate_login_page_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Files", "date": "", "value": "Added examples/login_page.html and orchestration artifacts under .vscode/tasks for planner-worker-reviewer flow.", "source": "session:orchestrate_login_page_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Conflict Resolution Policy", "date": "", "value": "Winner order: active status > higher priority > newer timestamp > higher source rank; only active winners are published in canonical memory.", "source": "memory/changelog/conflict_resolution_policy_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Orchestration Comparison", "date": "", "value": "Legacy setup had explicit orchestrator->planner/worker/reviewer/synthesizer/archivist delegation semantics, while current setup is role-based prompts/skills and lacks dedicated synthesizer+archivist enforcement and strict subagent isolation guarantees.", "source": "memory/changelog/orchestration_comparison_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Strict Orchestration Workflow", "date": "", "value": "State machine is mandatory: Planner -> (Worker<->Reviewer up to 3 attempts) -> Synthesizer after each APPROVE -> Archivist closure; halt and request human intervention on 3rd REJECT.", "source": "memory/changelog/strict_orchestration_state_machine_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "LLM Trace Visibility", "date": "", "value": "execute_repl_code returns llm_trace with truncated prompt/response previews for llm_query and llm_query_many calls; optional persistent JSONL trace is configurable.", "source": "memory/changelog/llm_trace_visibility_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "decision", "entity": "UI Auth + Car Shop Mock", "date": "", "value": "Expanded examples/login_page.html to include login, registration, and a static car store section with purchase simulation controls; no backend added.", "source": "session:orchestrate_auth_carshop_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "UI Buttons", "date": "", "value": "All action buttons in the auth and car-shop mock UI remain red, following the mandatory project button color policy.", "source": "session:orchestrate_auth_carshop_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Files", "date": "", "value": "Updated examples/login_page.html and orchestration artifacts under .vscode/tasks to reflect strict planner-worker-reviewer-synthesizer-archivist workflow for this session.", "source": "session:orchestrate_auth_carshop_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Local Iteration Logging", "date": "", "value": "Local iteration log file is rewritten on each new llm_query/llm_query_many request and stores only the current request iterations.", "source": "memory/changelog/local_iteration_log_overwrite_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "decision", "entity": "UI Theme Toggle", "date": "", "value": "Added light/dark mode toggle to examples/login_page.html with token-based styling and persisted theme selection in localStorage.", "source": "session:orchestrate_theme_toggle_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "UI Buttons", "date": "", "value": "All action buttons, including the theme toggle, remain red in both light and dark themes per project policy.", "source": "session:orchestrate_theme_toggle_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "change", "entity": "Files", "date": "", "value": "Updated examples/login_page.html and .vscode/tasks orchestration artifacts for strict planner-worker-reviewer-synthesizer-archivist execution in the theme-toggle session.", "source": "session:orchestrate_theme_toggle_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Local Iteration Logging", "date": "", "value": "local_llm_iterations.log is overwritten on each new local model request; for batch calls it stores all iterations of the current batch only.", "source": "memory/changelog/local_iteration_log_overwrite_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Orchestration Diagnostic Mode", "date": "", "value": "Use diagnostic:on for audit proof of role-stage invocations; use diagnostic:off to disable diagnostic logging and avoid extra overhead.", "source": "memory/changelog/orchestration_diagnostic_mode_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Communication Style", "date": "", "value": "Primary response template is defined in memory/canonical/communication.md (standard pattern: topic header, analysis/main content, summary/next steps), with structured/scannable formatting preferred.", "source": "session:memory_communication_template_check_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "UI Buttons", "date": "", "value": "User override applied: in examples/login_page.html light theme button tokens are green; dark theme button tokens remain red.", "source": "session:orchestrate_light_theme_green_buttons_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Slash Orchestrate Routing", "date": "", "value": "If prompt starts with /orchestrate, orchestrator must invoke .github/prompts/orchestrator_skill.prompt.md and delegate to subagents instead of doing implementation directly.", "source": "memory/changelog/slash_orchestrator_routing_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] {"type": "decision", "entity": "UI Selection Contract", "date": "2026-03-02", "value": "Implemented minimal car selection contract in examples/login_page.html via document-level event car:selected with payload { carId, modelPath } and no 3D engine initialization.", "source": "session:worker_task_01_ui_selection_contract_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "decision", "entity": "UI 3D Viewer Mount", "date": "2026-03-02", "value": "Defined explicit viewer mount point #carViewerMount in examples/login_page.html that updates placeholder state based on selected car payload.", "source": "session:worker_task_01_ui_selection_contract_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "decision", "entity": "UI 3D Viewer Integration", "date": "2026-03-02", "value": "Implemented lightweight CSS 3D rotating car visualization in #carViewerMount with no external dependencies and live variant switching from car:selected payload.", "source": "session:worker_task_02_3d_viewer_integration_20260302"} (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "UI 3D Fallback", "date": "2026-03-02", "value": "If .glb asset is unavailable, UI shows a visible warning fallback note while keeping rotating CSS 3D car preview active.", "source": "session:worker_task_02_3d_viewer_integration_20260302"} (source: session:unknown_session)
- [review][active;p=7] APPROVE for .vscode/tasks/task_03_validation_and_handoff.md: includes explicit Task01/Task02 criterion-by-criterion PASS statuses with evidence, concise Handoff/Caveats section, and scoped file-change list for no-git-metadata context. (source: session:unknown_session)
- [change][active;p=7] {"type": "rule", "entity": "Global MCP Server Routing", "date": "", "value": "Use fixed server command path with workspace-bound cwd and RLM_MEMORY_DIR (${workspaceFolder}/memory) to keep memory project-local while reusing one global MCP server codebase.", "source": "memory/changelog/global_server_per_project_memory_20260302.md"} (source: session:unknown_session)
- [change][active;p=7] MCP tools now support explicit project_path routing with isolated per-project MemoryStore and ReplRuntime caches. (source: session:unknown_session)
- [change][active;p=7] Added local-first memory compression path to reduce cloud context usage. (source: session:unknown_session)
- [change][active;p=7] Added local guide and rollback backup snapshot for local-first memory feature. (source: session:unknown_session)
- [change][active;p=7] Assessed external raw markdown memory corpus compatibility. (source: session:unknown_session)
- [change][active;p=7] Evaluated new-chat memory flow quality and model role split. (source: session:unknown_session)
- [change][active;p=7] Strengthened default local-first memory flow with one-call bootstrap and cheaper metadata defaults. (source: session:unknown_session)
- [change][active;p=7] Created comprehensive single-file context-window briefing for seamless cross-chat continuity. (source: session:unknown_session)
- [change][active;p=7] Audited last briefing-request flow for local-memory usage and token efficiency. (source: session:unknown_session)
- [change][active;p=7] Added codebase-to-RLM bootstrap generator for external projects. (source: session:unknown_session)
- [change][active;p=7] Implemented --emit-json-graph mode in codebase memory generator. (source: session:unknown_session)
- [change][active;p=7] Enforced English-only local model processing with separate user response language hint. (source: session:unknown_session)
- [change][active;p=7] Fixed user response language inference to prioritize chat language directives. (source: session:unknown_session)
- [change][active;p=7] Synchronized handoff documentation with current codebase capabilities and language policy. (source: session:unknown_session)
- [change][active;p=7] Added chat workflow files for one-shot codebase memory bootstrap execution. (source: session:unknown_session)

### verified_dark_theme_facts_presence_and_entity_rename
- [analysis][active;p=8] Verified user-provided mutation facts in external project memory: records exist in extracted_facts and canonical after manual fallback append plus consolidation; exact entity neon_glow_effects not present and appears as neon_glow_button_gradients. (source: session:copilot)
