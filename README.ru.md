# Hybrid RLM Memory MCP Server (Русская версия)

Python MCP-сервер для stateful REPL-процесса с запросами к локальной LLM и проектной памятью.

## Возможности

- Stateful Python REPL-инструмент: `execute_repl_code(code: str, project_path: str | None = None)`
- Вызовы локальной модели из REPL-глобалов: `llm_query(prompt)` и `llm_query_many(prompts, ...)`
- Хелперы финализации: `FINAL(text)` и `FINAL_VAR(var_name)`
- Предзагруженный контекст памяти: `memory_context`
- Диагностика памяти: `get_memory_metadata(project_path: str | None = None)`
- Локальный синтез памяти: `local_memory_brief(question: str, project_path: str | None = None, ...)`
- Локальный bootstrap в один вызов: `local_memory_bootstrap(question: str, project_path: str | None = None, ...)`
- Перезагрузка памяти: `reload_memory_context(project_path: str | None = None)`
- Консолидация канонической памяти: `consolidate_memory(..., project_path: str | None = None)`
- Предложение мутаций памяти: `propose_memory_mutation(query: str, action: str = "delete", ...)`
- Применение мутаций памяти: `apply_memory_mutation(mutation_plan: dict, ...)`

## Быстрый старт

1. Установите зависимости:

```bash
pip install -e .
```

2. Опционально задайте переменные окружения:

- `RLM_MEMORY_DIR` (по умолчанию: `memory`)
- `RLM_OLLAMA_URL` (по умолчанию: `http://127.0.0.1:11434`)
- `RLM_OLLAMA_MODEL` (по умолчанию: `qwen2.5-coder:14b`)
- `RLM_OLLAMA_TIMEOUT` (по умолчанию: `120`)
- `RLM_MAX_CONCURRENCY` (по умолчанию: `6`)
- `RLM_TRACE_PREVIEW_CHARS` (по умолчанию: `280`)
- `RLM_TRACE_PERSIST` (по умолчанию: `false`)
- `RLM_TRACE_FILE` (по умолчанию: `memory/logs/llm_trace.jsonl`)
- `RLM_LOCAL_ITER_LOG_ENABLED` (по умолчанию: `true`)
- `RLM_LOCAL_ITER_LOG_FILE` (по умолчанию: `memory/logs/local_llm_iterations.log`)
- `RLM_LOCAL_ITER_LOG_PREVIEW_CHARS` (по умолчанию: `420`)
- `RLM_LOCAL_LLM_FORCE_ENGLISH` (по умолчанию: `true`)
- `RLM_TIMESTAMP_MODE` (по умолчанию: `local`, варианты: `local|utc`)
- `RLM_MEMORY_MUTATION_MODE` (по умолчанию: `off`, варианты: `off|dry-run|on`)

3. Запустите сервер (stdio):

```bash
python -m rlm_mcp.server
```

## Глобалы внутри REPL

В `execute_repl_code` доступны:

- `memory_context: dict[str, str]`
- `llm_query(prompt: str) -> str`
- `llm_query_many(prompts: list[str], max_concurrency: int | None = None) -> list[str]`
- `FINAL(text: str) -> None`
- `FINAL_VAR(var_name: str) -> None`

Ответ `execute_repl_code` включает `llm_trace` с превью вызовов локальной модели:

- `call_type`, `ok`, `prompt_chars`, `response_chars`
- `prompt_preview`, `response_preview`
- batch-метаданные для `llm_query_many`

Если `RLM_TRACE_PERSIST=true`, все события трассировки дописываются в `memory/logs/llm_trace.jsonl`.

Поведение лога локальных итераций:

- Рантайм пишет события в `RLM_LOCAL_ITER_LOG_FILE`.
- На каждый новый запрос `llm_query` или `llm_query_many` файл перезаписывается с нуля.
- Для `llm_query_many` каждая пара prompt/response сохраняется как отдельная итерация.

## API консолидации

```text
consolidate_memory(
  log_rel_path: str = "logs/extracted_facts.jsonl",
  write_changelog: bool = True,
  refresh_context: bool = True,
  project_path: str | None = None,
  summarize_old_changelogs: bool = True,
  older_than_days: int = 2,
  keep_raw_changelogs: bool = False,
  max_files_per_summary: int = 20,
  max_changelog_files_trigger: int = 40,
  max_changelog_bytes_trigger: int = 25000
) -> dict
```

Возвращает счётчики и пути:

- `total_log_records`, `extracted_fact_records`, `unique_facts`
- `architecture_items`, `coding_rules_items`, `active_tasks_items`
- `architecture_path`, `coding_rules_path`, `active_tasks_path`, `changelog_path`
- `reloaded_files` (если `refresh_context=True`)
- `summaries_created`, `raw_files_summarized`, `raw_files_archived` (если суммаризация включена)

## API мутаций памяти (под feature flag)

Режим работы:

- `RLM_MEMORY_MUTATION_MODE=off` (по умолчанию): применение мутаций заблокировано
- `RLM_MEMORY_MUTATION_MODE=dry-run`: предложение работает, применение заблокировано
- `RLM_MEMORY_MUTATION_MODE=on`: предложение и применение включены

### `propose_memory_mutation(...)`

```text
propose_memory_mutation(
  query: str,
  action: str = "delete",
  replacement_value: str | None = None,
  project_path: str | None = None,
  max_matches: int = 3
) -> dict
```

Поведение:

- Ищет кандидаты среди extracted facts (lexical scoring по `entity/value/source/type`)
- Поддерживает `action`: `delete`, `update`
- Для `update` обязателен `replacement_value`
- Ничего не записывает в файлы памяти
- Возвращает ранжированные кандидаты и исполнимый `mutation_plan`

### `apply_memory_mutation(...)`

```text
apply_memory_mutation(
  mutation_plan: dict,
  project_path: str | None = None
) -> dict
```

Поведение:

- Валидирует операции по строгой схеме extracted-fact
- Добавляет записи в `memory/logs/extracted_facts.jsonl`
- Запускает консолидацию и перепубликацию canonical-файлов
- Перезагружает memory context рантайма
- Пишет аудит в `memory/logs/memory_mutations.jsonl`

Семантика:

- `delete` = добавить `deprecated`-запись для найденного активного факта
- `update` = добавить `deprecated` для старого факта + `active` upsert для нового
- Канонические файлы обновляются только через консолидацию

Гарантия non-impact:

- Базовые потоки (`execute_repl_code`, `local_memory_bootstrap`, `local_memory_brief`, обычные save-memory сценарии) не меняются.
- Логика мутаций изолирована отдельными инструментами и флагом.

## Компактный режим метаданных

`get_memory_metadata` по умолчанию возвращает экономичный вывод:

- `max_files=20`
- `include_headers=false`
- `include_files=false`
- `sort_by="chars_desc"`

Даже в компактном режиме возвращаются агрегаты:

- `total_files`, `total_chars`, `total_lines`, `truncated`

## Local-first режим (рекомендуется)

Используйте `local_memory_brief(question, project_path=...)` для локального retrieval+synthesis и передачи в cloud только компактного результата.

Языковая политика:

- Локальная модель по умолчанию работает на английском (`RLM_LOCAL_LLM_FORCE_ENGLISH=true`).
- Язык ответа пользователю должен следовать настройкам коммуникации из памяти.

Для старта в один шаг используйте `local_memory_bootstrap(question, project_path=...)`.

Типичный поток:

1. `local_memory_bootstrap(question="...", project_path="<active_workspace_root>")`
2. Cloud-модель использует `brief`, `selected_files`, `memory_stats`
3. При необходимости углубляется через `local_memory_brief`/`execute_repl_code`

## Cloud payload аудит

- Основные ответы MCP-инструментов дописываются в `memory/logs/cloud_payload_audit.md`.
- Последний snapshot перезаписывается в `memory/logs/cloud_payload_current.md`.
- Каждая запись содержит имя инструмента, размер payload, оценку токенов, top-level keys и превью.

## Быстрая диагностика

- Факт не попал в canonical: проверьте `memory/logs/extracted_facts.jsonl`, затем блок `consolidate_memory` в `memory/logs/cloud_payload_current.md`.
- Несоответствие между инструментом и ответом в чате: проверьте `memory/logs/cloud_payload_current.md` и историю в `memory/logs/cloud_payload_audit.md`.
- Локальные итерации модели: проверьте `memory/logs/local_llm_iterations.log`.

## Модель «глобальный сервер + память на проект»

Рекомендуется:

- Держать `command` на Python-окружение этого репозитория (глобальная кодовая база MCP-сервера)
- Держать `cwd` на пути этого репозитория
- Передавать `project_path` во все memory-sensitive вызовы

Так одна кодовая база сервера переиспользуется между проектами, а память остаётся изолированной внутри каждого `<project>/memory`.

## Copilot Autopilot Mode

В проекте есть `.github/copilot-instructions.md`:

- Copilot автоматически загружает memory context перед задачей
- После задачи автоматически пишет факт в memory log и запускает `consolidate_memory()`
- Чтобы отключить это на один запрос, добавьте фразу: `skip memory update`

## Минимальная команда bootstrap-импорта

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([ScriptBlock]::Create((Invoke-WebRequest 'https://raw.githubusercontent.com/dvgmdvgm/rlm_by_5.3Codex_VSCode/main/scripts/rlm/install_rlm_bootstrap.ps1' -UseBasicParsing).Content))"
```

По умолчанию импортируются:

- `.github/`
- `scripts/rlm/generate_rlm_memory_from_code.py`
- `scripts/rlm/seed_canonical_from_rlm_memory.py`
- `scripts/rlm/write_orchestrator_memory_checklist.py`

## Полезные документы и скрипты

- Режим логирования cloud payload:
  - `memory/logs/cloud_payload_audit.md` — компактный append-only лог (`payload_preview`).
  - `memory/logs/cloud_payload_current.md` — перезаписываемый снимок с полным payload (`payload_full`).
- Скрипт self-check режима payload:
  - `scripts/rlm/check_cloud_payload_mode.ps1`
  - Пример: `powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\rlm\\check_cloud_payload_mode.ps1 -ProjectRoot "D:/your/project"`
- `docs/context-window-briefing.md`
- `docs/local-first-memory-guide.md`
- `docs/codebase-to-rlm-memory-workflow.md`
- `docs/github-bootstrap-install.md`
- `docs/memory-mutation-maintenance-checklist.md`
- `scripts/rlm/generate_rlm_memory_from_code.py`
- `scripts/rlm/seed_canonical_from_rlm_memory.py`
- `scripts/rlm/check_cloud_payload_mode.ps1`
- `scripts/rlm/migrate_legacy_facts.py`
- `scripts/rlm/install_rlm_bootstrap.ps1`
- `backups/pre_local_first_20260302/restore.ps1`

## Чеклист handoff для нового контекстного окна

Передавайте в первую очередь:

- `docs/context-window-briefing.md`
- `.github/copilot-instructions.md`
- `README.md`
- `README.ru.md`
- `docs/local-first-memory-guide.md`
- `docs/codebase-to-rlm-memory-workflow.md`
