# Codebase → RLM Memory Workflow

## Что это

Это запускной workflow через скрипт, который строит новую RLM-структуру памяти **из кода проекта**, не опираясь на существующие memory-файлы.

Скрипт:
- `scripts/generate_rlm_memory_from_code.py`
- `scripts/seed_canonical_from_rlm_memory.py`

Chat workflow files:
- Prompt file: `.github/prompts/bootstrap_memory_from_codebase.prompt.md`
- Command file: `.github/commands/bootstrap-memory.md`

## Что он делает

1. Рекурсивно сканирует кодовую базу (web + mobile + backend).
2. Определяет технологический стек, зависимости и признаки фреймворков.
3. Извлекает маршруты/API-сигналы, сущности, import-связи, test-файлы.
4. Анализирует стилевые паттерны (цвета, animation-сигналы, css/tailwind).
5. Формирует RLM-совместимую memory-структуру в 13 категориях.
6. Генерирует файлы с inferred-решениями и пометками confidence.
7. Заполняет `memory/logs/extracted_facts.jsonl` из `rlm_memory/*` и запускает консолидацию в `memory/canonical/*`.

## Важно

- Анализ делается по коду и конфигам.
- Это bootstrap-память: для критичных решений нужна валидация человеком.
- Старые memory-файлы не требуются для генерации.

## Запуск (рекомендуемый)

Из этого репозитория:

```powershell
python scripts/generate_rlm_memory_from_code.py --project-root "D:/path/to/your/other-project"
python scripts/seed_canonical_from_rlm_memory.py --project-root "D:/path/to/your/other-project"
```

Результат по умолчанию:

- `D:/path/to/your/other-project/memory/rlm_memory/`

## Запуск с кастомным output

```powershell
python scripts/generate_rlm_memory_from_code.py \
  --project-root "D:/path/to/your/other-project" \
  --output-dir "D:/path/to/your/other-project/memory/rlm_memory_bootstrap"
```

## Опции

- `--max-file-chars 160000` — лимит чтения одного файла
- `--include-hidden` — включать скрытые папки (кроме hard-ignored)
- `--emit-json-graph` — дополнительно генерировать JSON-граф модулей/связей
- `--graph-file "<path>"` — кастомный путь для графа (по умолчанию `<output-dir>/code_graph.json`)

## Пример с JSON-графом

```powershell
python scripts/generate_rlm_memory_from_code.py \
  --project-root "D:/path/to/your/other-project" \
  --emit-json-graph
```

Результат:

- `<output-dir>/code_graph.json`

Содержимое графа:

- `nodes` — source/external узлы
- `edges` — import-связи с признаком `is_internal`
- `stats` — количество узлов/ребер, internal/external breakdown

## Какая структура создаётся

Внутри output будет создано:

- `01_project/`
- `02_architecture/`
- `03_decisions/`
- `04_domain/`
- `05_code/`
- `06_problems/`
- `07_context/`
- `08_people/`
- `09_external/`
- `10_testing/`
- `11_deployment/`
- `12_roadmap/`
- `13_preferences/`
- `scan_manifest.json`

## Следующий шаг после генерации

1. Просмотреть `03_decisions/inferred_decisions.md`.
2. Проверить заполнение `memory/canonical/architecture.md`, `memory/canonical/coding_rules.md`, `memory/canonical/active_tasks.md`.
3. Подтвердить/исправить критичные выводы (архитектура, домен, деплой).
4. Подключить проект к нашему MCP серверу и выполнить:
   - `local_memory_bootstrap(...)`
   - затем рабочие задачи в новом контекстном окне.

## Когда это особенно полезно

- первый запуск на новом крупном проекте,
- миграция между чатами/контекстными окнами,
- регулярный пересъём памяти после больших рефакторингов.

## Быстрый запуск из чата (без ручной команды)

1. В Copilot Prompt Picker выберите:
  - `.github/prompts/bootstrap_memory_from_codebase.prompt.md`
2. Либо используйте команду проекта:
  - `/bootstrap-memory`

Если slash-команда не отображается в UI, используйте prompt-file вариант (он надёжнее в разных клиентах).
