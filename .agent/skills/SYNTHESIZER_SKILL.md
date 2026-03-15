---
name: Synthesizer
description: Memory-sync and operational-rules gate for Antigravity orchestration. Use immediately after a task is approved to persist extracted facts, consolidate memory, evaluate all active operational rules, and decide whether the workflow may advance.
---

# Synthesizer Skill

## Mission

After every approved task, synchronize implementation knowledge into project memory and enforce operational rules for the current task.

## Mandatory gate block

```text
### SYNTHESIZER GATE — Task <ID>
- MEMORY_SYNC_OK: yes/no
- RULES_CHECKED: <N>
- RULES_MATCHED: <N>
- RULES_EXECUTED: <N>
- RULES_FAILED_BLOCKING: <N>
- RULES_EVIDENCE_COMPLETE: yes/no
- OP_RULES_OK: yes/no
- SYNTHESIZER_GATE_PASSED: yes/no
```

## Mandatory behavior

- append structured session facts to `memory/logs/extracted_facts.jsonl`
- run `consolidate_memory(project_path=<active_workspace_root>)`
- evaluate all active rules from canonical memory and extracted facts
- capture execution evidence for every matched rule
- block advancement if memory sync or rules gating fails
