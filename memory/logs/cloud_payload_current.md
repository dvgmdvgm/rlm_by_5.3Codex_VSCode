# Current Cloud Payload Snapshot

This file is overwritten on each payload transfer to cloud-facing response channel.
It stores the full payload without compact preview truncation.
---
ts: 2026-04-04T13:02:51.842815+02:00
tool: smart_exec
project_path: d:\AI Projects\VSCode_Projects\RLM_Realization
memory_dir: d:/AI Projects/VSCode_Projects/RLM_Realization/memory
payload_chars: 479
payload_est_tokens: 119
payload_keys: command, command_type, compressed_output, cwd, exit_code, savings
payload_full:
```json
{
  "command": "& \"d:/AI Projects/VSCode_Projects/RLM_Realization/.venv/Scripts/python.exe\" -m pytest tests/test_command_runner.py tests/test_powershell_fixer.py -q",
  "cwd": "d:\\AI Projects\\VSCode_Projects\\RLM_Realization",
  "compressed_output": "PASSED: 1 tests",
  "exit_code": 0,
  "command_type": "pytest",
  "savings": {
    "original_chars": 738,
    "compressed_chars": 15,
    "original_tokens_est": 184,
    "compressed_tokens_est": 3,
    "savings_pct": 98.0,
    "strategies": [
      "filter",
      "group"
    ]
  }
}
```
