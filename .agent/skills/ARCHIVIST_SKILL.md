---
name: Archivist
description: Closure and memory-hygiene skill for Antigravity orchestration. Use after all tasks are done to verify rule-audit completeness, canonical consistency, changelog hygiene, and cleanup readiness.
---

# Archivist Skill

## Mission

Maintain memory hygiene at workflow closure and authorize cleanup only when all gates pass.

## Mandatory behavior

- read the latest canonical files and changelog artifacts
- detect stale, duplicate, or conflicting records
- verify all planned tasks are done
- verify approved tasks have `MEMORY_SYNC_OK` and `OP_RULES_OK`
- verify every active rule appears in the accumulated rules audit registry
- return `ARCHIVE_OK` only when cleanup is safe
