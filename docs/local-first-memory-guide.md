# Local-First Memory Guide

## Зачем это нововведение

Цель: уменьшить расход cloud-контекста за счёт переноса тяжёлой работы с памятью на локальную модель.

Было:
- в облако часто уходили длинные результаты `get_memory_metadata`
- в облако уходили крупные фрагменты memory-документов

Стало:
- локальная модель сама выбирает релевантные memory-файлы
- локальная модель формирует короткий `brief`
- в облако передаётся в основном `brief` + список источников
- единый bootstrap-call подготавливает контекст и языковые подсказки

## Что изменилось в MCP tools

1. `get_memory_metadata(...)`
- добавлены параметры компактного режима:
  - `max_files` (по умолчанию 20)
  - `include_headers` (по умолчанию false)
  - `include_files` (по умолчанию false)
  - `sort_by` (`chars_desc` по умолчанию)
- добавлены агрегаты:
  - `total_files`, `total_chars`, `total_lines`, `truncated`

2. `local_memory_brief(...)`
- новый tool для local-first свёртки памяти
- принимает:
  - `question`
  - `project_path`
  - `max_files`
  - `max_chars_per_file`
- возвращает:
  - `brief`
  - `selected_files`
  - `selected_count`

3. `local_memory_bootstrap(...)`
- единый вход для нового контекстного окна:
  - reload memory
  - compact metadata (aggregate-only)
  - local brief
- дополнительно возвращает:
  - `local_model_output_language`
  - `user_response_language`

4. Language policy
- локальная модель: English-only (по умолчанию `RLM_LOCAL_LLM_FORCE_ENGLISH=true`)
- язык ответа пользователю: из `user_response_language` (из memory canonical preferences)

## Рекомендуемый поток для коротких factual-запросов

1. `local_memory_bootstrap(question="...", project_path=<active_workspace_root>)`
2. Использовать `brief`, `selected_files`, `user_response_language`
3. В облако отправлять только:
  - `brief`
  - `selected_files` (опционально)
  - `memory_stats` (если нужны только агрегаты)

## Рекомендуемый поток для сложных запросов

1. Сначала `local_memory_bootstrap(...)`
2. Если ответа недостаточно:
  - `local_memory_brief(..., max_files↑, max_chars_per_file↑)`
3. Если всё ещё недостаточно:
  - `execute_repl_code(..., project_path=...)` с локальными `llm_query/llm_query_many`
4. В облако отправлять только итоговую выжимку

## Пример

Вопрос: «Сколько экранов у мобильного приложения?»

Экономный путь:
1. `local_memory_bootstrap(question="Сколько экранов у мобильного приложения?", project_path="d:/art_network_antigravity", max_files=6)`
2. Облачная модель получает короткий `brief` от локальной модели
3. Облачная модель отвечает пользователю на языке из `user_response_language`

## Откат

Для отката к версии до local-first нововведения используйте:

- `backups/pre_local_first_20260302/restore.ps1`

Скрипт восстанавливает:
- `src/rlm_mcp/server.py`
- `README.md`
- `.github/copilot-instructions.md`

## Проверка после отката

1. Перезапустить MCP сервер.
2. Убедиться, что в `src/rlm_mcp/server.py` нет `local_memory_brief`.
3. Убедиться, что `get_memory_metadata` снова без расширенных параметров.

## Проверка актуального режима

1. Вызвать `local_memory_bootstrap(...)`.
2. Проверить поля:
  - `local_model_output_language == "en"`
  - `user_response_language` соответствует правилам из `memory/canonical/communication.md`
