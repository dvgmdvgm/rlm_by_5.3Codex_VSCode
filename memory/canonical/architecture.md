# Canonical Architecture Memory

## META
- id: architecture
- updated_at: 2026-03-12T09:26:14.182416+01:00
- source: memory/logs/extracted_facts.jsonl
- items: 13

### autopilot_orchestrator_mode_override
- [architecture][active;p=9] Added ORCHESTRATOR MODE OVERRIDE section to copilot-instructions.md. When orchestration is active, Primary Goal, Sections B/B1/B2/C, Autonomy Policy, and Response Style are SUSPENDED. Only HARD GATE, Section A, Safety, and Slash Commands remain active. Slash Commands moved up near HARD GATE for higher LLM attention weight. All suspended sections marked [DIRECT MODE ONLY] with warning blocks. (source: session:autopilot_orchestrator_conflict_fix)

### changelog_retention
- [architecture][active;p=7] Added auto-summarization pipeline for old rlm_consolidation changelogs into monthly summaries with optional archival of raw files. (source: session:auto_summarize_old_changelogs)

### code_index_dependencies
- [architecture][active;p=6] Code index uses tree-sitter>=0.24 with individual language packages (tree-sitter-python, tree-sitter-javascript, etc.) as optional dependencies in pyproject.toml [project.optional-dependencies] code-index group. (source: session:copilot)

### consolidate_memory_tool
- [api][active;p=8] Extended consolidate_memory with summarize_old_changelogs, older_than_days, keep_raw_changelogs, max_files_per_summary. (source: session:consolidate_memory_api_update)

### copilot_bridge_extension_agent_mode
- [architecture][active;p=9] VS Code extension (TypeScript, 528 lines) runs in Agent Mode with 7 tools: file_tree, list_dir, read_file, write_file, edit_file, search_files, run_terminal. Uses vscode.lm Language Model API. Agent loop with max 15 iterations. LLM outputs ```tool_call``` blocks, extension parses and executes them. File: copilot-bridge/extension/src/extension.ts. (source: session:bridge_memory_save)

### copilot_bridge_extension_config
- [architecture][active;p=7] Extension settings: copilotBridge.relayUrl (ws://localhost:8765/ws), copilotBridge.token, copilotBridge.autoConnect (bool), copilotBridge.modelFamily. Commands: copilotBridge.connect, copilotBridge.disconnect, copilotBridge.showStatus. Package: copilot-bridge v0.1.0, publisher rlm-realization, vscode ^1.95.0. (source: session:bridge_memory_save)

### copilot_bridge_message_protocol
- [architecture][active;p=8] All messages are JSON over WebSocket: {type, id, ts, payload}. Types: prompt (phone->vscode), chunk/complete/error/status/tool_call/tool_result (vscode->phone), cancel (phone->vscode), peer_status (relay->both), ping/pong (bidirectional). (source: session:bridge_memory_save)

### copilot_bridge_pwa
- [architecture][active;p=8] Phone PWA: dark VS Code-inspired theme, markdown rendering (marked.js), WebSocket client, localStorage chat persistence, auto-reconnect, tool_call/tool_result rendering with icons. Files: copilot-bridge/web/index.html, app.js (565+ lines), style.css (650+ lines), manifest.json, sw.js. (source: session:bridge_memory_save)

### copilot_bridge_relay_server
- [architecture][active;p=8] Relay server: FastAPI + WebSocket on port 8765. Brokers messages between phone and VS Code. Serves PWA static files from ../web via StaticFiles mount. API routes under /api/ prefix (health, status, history). Auth via ?token= query param. File: copilot-bridge/relay/main.py (290 lines). (source: session:bridge_memory_save)

### copilot_bridge_security
- [architecture][active;p=7] Security model: shared secret token generated via generate_token.py (32-byte URL-safe base64). Token sent as query param on WebSocket upgrade. Relay validates token on connection. For production: use WSS with TLS behind nginx/Caddy. (source: session:bridge_memory_save)

### copilot_bridge_tool_protocol
- [architecture][active;p=8] Agent tool protocol: LLM outputs ```tool_call {name, args}``` code blocks. Extension parses via regex, dispatches to tool functions, sends tool_call/tool_result messages to phone for UI rendering. If no tool calls in LLM output, agent loop ends. Tool results fed back as User messages for next iteration. (source: session:bridge_memory_save)

### copilot_bridge_websocket_flow
- [architecture][active;p=7] WebSocket flow: Phone connects to relay with token -> auth message -> relay registers as phone client. Extension connects similarly -> auth as vscode. Relay forwards messages between them. Auto-reconnect with 5s delay on unexpected close. Ping every 30s keepalive. (source: session:bridge_memory_save)

### orchestrator_context_resilience_checkpoint
- [architecture][active;p=9] Added context resilience mechanism to orchestrator: checkpoint file (.vscode/tasks/orchestrator_state.json) written after every state transition, mandatory re-orientation step (re-read checkpoint + master_plan + protocol reminder) before every new task and before closure. Solves context window degradation in long orchestration runs where LLM forgets instructions, skips archivist, and fails to clean .vscode/tasks/. (source: session:context_resilience_fix)
