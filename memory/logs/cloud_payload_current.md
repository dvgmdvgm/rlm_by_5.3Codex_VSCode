# Current Cloud Payload Snapshot

This file is overwritten on each payload transfer to cloud-facing response channel.
It stores the full payload without compact preview truncation.
---
ts: 2026-04-02T02:57:41.516689+02:00
tool: smart_exec
project_path: d:\AI Projects\VSCode_Projects\RLM_Realization
memory_dir: d:/AI Projects/VSCode_Projects/RLM_Realization/memory
payload_chars: 473
payload_est_tokens: 118
payload_keys: command, command_type, compressed_output, cwd, exit_code, has_error, savings, timed_out, timeout_type
payload_full:
```json
{
  "command": "\"C:\\Program Files\\Git\\cmd\\git.exe\" -C \"d:\\AI Projects\\VSCode_Projects\\RLM_Realization\" status --short",
  "cwd": "d:\\AI Projects\\VSCode_Projects\\RLM_Realization",
  "compressed_output": "",
  "exit_code": 1,
  "command_type": "empty",
  "savings": {
    "original_chars": 0,
    "compressed_chars": 0,
    "original_tokens_est": 1,
    "compressed_tokens_est": 1,
    "savings_pct": 0.0,
    "strategies": [
      "none"
    ]
  },
  "timed_out": true,
  "timeout_type": "startup",
  "has_error": true
}
```
