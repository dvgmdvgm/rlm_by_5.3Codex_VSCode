User: Hello! what's our project about?

GitHub Copilot: I’ll quickly load the project memory context first, then summarize the project purpose in plain language from canonical sources.

Ran `local_memory_bootstrap` 
Completed with input: {
  "question": "Summarize what this project is about at a high level",
  "project_path": "d:\\AI Projects\\VSCode_Projects\\RLM_Realization",
  "max_files": 8,
  "max_chars_per_file": 3500
}

I’ve loaded the memory brief; next I’m pulling quick memory metadata to confirm the canonical scope before I summarize.

Ran `get_memory_metadata` 
Completed with input: {
  "project_path": "d:\\AI Projects\\VSCode_Projects\\RLM_Realization",
  "max_files": 20,
  "include_headers": false,
  "include_files": false
}

This project is a Python-based **RLM Memory MCP server**: an “autopilot memory layer” for coding agents.

- It helps agents load project context first, then do work, then save/consolidate new facts so memory stays current.
- It uses a **hybrid local-first workflow**: a local Sub-LM handles memory-heavy summarization/extraction, while the cloud model makes higher-level decisions.
- It keeps long-lived knowledge in memory (canonical rules, architecture, active tasks, changelog, extracted facts).
- It also defines agent workflow and communication standards so outputs are structured, concise, and consistent.

If you want, I can also give you a 60-second tour of the most important files to read first.