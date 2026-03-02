# Canonical Active Tasks Memory

## META
- id: active_tasks
- updated_at: 2026-03-02T12:17:02.554117+00:00
- source: memory/logs/extracted_facts.jsonl
- items: 31

### Agentic Workflow
- [rule][active;p=0] Planner queries RLM first, Worker queries targeted memory before coding, Reviewer enforces APPROVE/REJECT gate. (source: memory/changelog/memory_reset_20260302.md)

### Archivist Closure Pass
- [task][active;p=0] Closure audit for car-selection 3D orchestration run (diagnostic:off): planned tasks in .vscode/tasks/master_plan.md are marked complete and reviewer approvals are present for Task 01/02/03 (Task 03 via re-review). (source: session:archivist_closure_pass_20260302)

### Archivist Closure Recheck
- [task][active;p=0] Post-remediation recheck confirms Task 01/02/03 are complete with approvals present and per-approved-task memory sync evidence available (Task 01 explicit gate file with MEMORY_SYNC_OK; Task 02/03 synthesizer gate evidence in extracted facts). Final closure status: no blockers. (source: session:archivist_closure_recheck_post_task01_gate_20260302)

### Baseline Tasks
- [task][active;p=0] Keep memory project-specific and continue canonical consolidation after major sessions. (source: memory/changelog/memory_reset_20260302.md)

### bootstrap_install
- [task][active;p=6] Added scripts/install_rlm_bootstrap.ps1 to install only reusable integration assets via sparse checkout (excluding server source). (source: session:github_bootstrap_installer)

### Communication Style
- [rule][active;p=0] Primary response template is defined in memory/canonical/communication.md (standard pattern: topic header, analysis/main content, summary/next steps), with structured/scannable formatting preferred. (source: session:memory_communication_template_check_20260302)

### Files
- [change][active;p=0] Added examples/login_page.html and orchestration artifacts under .vscode/tasks for planner-worker-reviewer flow. (source: session:orchestrate_login_page_20260302)
- [change][active;p=0] Updated examples/login_page.html and orchestration artifacts under .vscode/tasks to reflect strict planner-worker-reviewer-synthesizer-archivist workflow for this session. (source: session:orchestrate_auth_carshop_20260302)
- [change][active;p=0] Updated examples/login_page.html and .vscode/tasks orchestration artifacts for strict planner-worker-reviewer-synthesizer-archivist execution in the theme-toggle session. (source: session:orchestrate_theme_toggle_20260302)
- [change][active;p=0] Updated examples/login_page.html for Task 01 only: added selection payload attributes on car buttons, added #carViewerMount container, and wired car:selected dispatch/listener contract. (source: session:worker_task_01_ui_selection_contract_20260302)
- [change][active;p=0] Updated examples/login_page.html for Task 02: added CSS 3D scene, rotating car model mock, carId-based visual variants, asset availability check, and live viewer status messaging without backend. (source: session:worker_task_02_3d_viewer_integration_20260302)

### Global MCP Server Routing
- [rule][active;p=0] Use fixed server command path with workspace-bound cwd and RLM_MEMORY_DIR (${workspaceFolder}/memory) to keep memory project-local while reusing one global MCP server codebase. (source: memory/changelog/global_server_per_project_memory_20260302.md)

### Memory Sync Gate Coverage
- [task][active;p=0] Evidence exists for synthesizer memory sync on Task 02 and Task 03; no explicit standalone Task 01 memory-sync gate artifact was found, so strict per-approved-task gate traceability is partially blocked. (source: session:archivist_closure_pass_20260302)
- [task][active;p=0] Task 01 gate remediation completed: per-approved-task evidence now exists for Task 01/02/03 (Task 01 explicit .vscode/tasks/task_01_memory_sync_gate.md with MEMORY_SYNC_OK; Task 02 and Task 03 synthesizer gate evidence recorded in memory/logs/extracted_facts.jsonl). No remaining gate blocker for closure. (source: session:archivist_closure_recheck_post_task01_gate_20260302)

### Orchestrate Invocation
- [rule][active;p=0] Use .github/prompts/orchestrate.prompt.md as primary entrypoint when /orchestrate is not visible in chat UI. (source: memory/changelog/orchestrate_promptfile_fix_20260302.md)

### Orchestration Comparison
- [rule][active;p=0] Legacy setup had explicit orchestrator->planner/worker/reviewer/synthesizer/archivist delegation semantics, while current setup is role-based prompts/skills and lacks dedicated synthesizer+archivist enforcement and strict subagent isolation guarantees. (source: memory/changelog/orchestration_comparison_20260302.md)

### Planner Artifacts
- [task][active;p=0] Created minimal planning artifacts for car-selection 3D rotating visualization request (diagnostic:off): updated .vscode/tasks/master_plan.md and added task_01_ui_selection_contract.md, task_02_3d_viewer_integration.md, task_03_validation_and_handoff.md; planning-only, no code implementation. (source: session:planner_car_3d_visualization_20260302)

### RLM MCP Server
- [rule][active;p=0] Project is a Python MCP server implementing Hybrid RLM memory workflow. (source: memory/changelog/memory_reset_20260302.md)

### Slash Orchestrate Routing
- [rule][active;p=0] If prompt starts with /orchestrate, orchestrator must invoke .github/prompts/orchestrator_skill.prompt.md and delegate to subagents instead of doing implementation directly. (source: memory/changelog/slash_orchestrator_routing_20260302.md)

### Strict Orchestration Workflow
- [rule][active;p=0] State machine is mandatory: Planner -> (Worker<->Reviewer up to 3 attempts) -> Synthesizer after each APPROVE -> Archivist closure; halt and request human intervention on 3rd REJECT. (source: memory/changelog/strict_orchestration_state_machine_20260302.md)

### Task 01 Memory Sync Gate
- [review][active;p=0] Re-ran memory sync and created explicit gate artifact .vscode/tasks/task_01_memory_sync_gate.md containing required MEMORY_SYNC_OK marker after approved Task 01 outcomes. (source: session:synthesizer_task_01_memory_gate_20260302)

### Task 01 UI Selection Contract
- [review][active;p=0] Reviewer verdict APPROVE: minimal selection contract and explicit #carViewerMount are present in examples/login_page.html; no additional task-01-unrelated UX changes detected in worker scope artifacts. (source: session:reviewer_task_01_ui_selection_contract_20260302)

### Task 02 3D Viewer Integration
- [review][active;p=0] Reviewer gate APPROVE confirmed for .vscode/tasks/task_02_3d_viewer_integration.md: selected car display, continuous rotation, selection switch update, and visible missing-model fallback requirements are accepted. (source: session:synthesizer_task_02_memory_gate_20260302)

### Task 03 Validation + Handoff
- [change][active;p=0] Validated Task 01/02 acceptance criteria directly in examples/login_page.html and updated .vscode/tasks/master_plan.md with completed statuses and caveat that examples/assets/models/* is absent and viewer uses CSS 3D fallback without real GLB renderer. (source: session:worker_task_03_validation_handoff_20260302)
- [review][active;p=0] Synthesizer memory gate executed after reviewer APPROVE; Task 01 and Task 02 acceptance criteria recorded as PASS with evidence and caveats documented in .vscode/tasks/task_03_validation_and_handoff.md. (source: session:synthesizer_task_03_memory_gate_20260302)

### UI 3D Fallback
- [rule][active;p=0] If .glb asset is unavailable, UI shows a visible warning fallback note while keeping rotating CSS 3D car preview active. (source: session:worker_task_02_3d_viewer_integration_20260302)

### UI 3D Viewer Integration
- [decision][active;p=0] Implemented lightweight CSS 3D rotating car visualization in #carViewerMount with no external dependencies and live variant switching from car:selected payload. (source: session:worker_task_02_3d_viewer_integration_20260302)

### UI 3D Viewer Mount
- [decision][active;p=0] Defined explicit viewer mount point #carViewerMount in examples/login_page.html that updates placeholder state based on selected car payload. (source: session:worker_task_01_ui_selection_contract_20260302)

### UI Buttons
- [rule][active;p=0] Mandatory rule: for future web page layout tasks, all site buttons must be red unless explicitly overridden by the user for that task. (source: memory/changelog/button_color_rule_20260302.md)

### UI Login Page
- [decision][active;p=0] Implemented a static login page without backend logic containing username/password fields and a submit button. (source: session:orchestrate_login_page_20260302)

### UI Selection Contract
- [decision][active;p=0] Implemented minimal car selection contract in examples/login_page.html via document-level event car:selected with payload { carId, modelPath } and no 3D engine initialization. (source: session:worker_task_01_ui_selection_contract_20260302)
