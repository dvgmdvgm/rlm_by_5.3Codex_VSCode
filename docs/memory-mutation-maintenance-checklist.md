# Memory Mutation Maintenance Checklist

Короткий операторский протокол для безопасного удаления/обновления данных памяти.

## 0) Цель

Использовать mutation-tools так, чтобы:
- не ломать обычные read/save флоу,
- не удалить лишние факты,
- сохранить аудит и повторяемость.

## 1) Pre-check

- Убедиться, что работа идёт в нужном проекте (`project_path=<active_workspace_root>`).
- Выполнить `local_memory_bootstrap(question=..., project_path=...)`.
- Проверить, что память доступна и `memory_dir` указывает на целевой проект.
- Снять baseline по canonical (минимум: `coding_rules.md`, `active_tasks.md`, `architecture.md`).

## 2) Выбор режима

- По умолчанию: `RLM_MEMORY_MUTATION_MODE=off`.
- Для анализа кандидатов: `RLM_MEMORY_MUTATION_MODE=dry-run`.
- Для реального применения (только после review): `RLM_MEMORY_MUTATION_MODE=on`.

Рекомендация: не оставлять `on` после завершения maintenance-сессии.

## 3) Proposal-only этап

1. Вызвать `propose_memory_mutation(...)` с естественным запросом.
2. Проверить `matches`:
   - релевантность (`score`),
   - что это действительно нужные `entity/value/source`,
   - нет ли пересечения с критичными активными правилами.
3. Проверить `mutation_plan`:
   - операции `deprecate/upsert` соответствуют ожидаемому результату,
   - при `update` корректен `replacement_value`.

Если есть сомнения — сузить запрос и повторить proposal.

## 4) Apply этап (только в `on`)

1. Переключить `RLM_MEMORY_MUTATION_MODE=on`.
2. Выполнить `apply_memory_mutation(mutation_plan=..., project_path=...)`.
3. Убедиться, что:
   - `ok=true`,
   - есть `records_appended > 0`,
   - consolidation завершился успешно.

## 5) Post-check

- Проверить canonical после apply:
  - удалённые факты больше не активны в canonical,
  - обновления отображаются корректно.
- Проверить аудит:
  - `memory/logs/memory_mutations.jsonl`,
  - `memory/logs/cloud_payload_audit.md`.
- Выполнить повторный `local_memory_bootstrap(...)` для обновлённого контекста.

## 6) Завершение сессии

- Вернуть режим в безопасное состояние: `RLM_MEMORY_MUTATION_MODE=off`.
- Зафиксировать ключевой итог в `memory/logs/extracted_facts.jsonl`.
- Выполнить `consolidate_memory(project_path=...)`.
- При необходимости: commit + push.

## 7) Stop conditions

Остановить apply и вернуться к proposal/review, если:
- запрос слишком широкий и `matches` содержат нерелевантные факты,
- в плане присутствуют критичные правила без явного подтверждения,
- контекст проекта/`memory_dir` не совпадает с целевым проектом.
