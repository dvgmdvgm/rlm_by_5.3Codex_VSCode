# REPL Workflow Example (Chunking + Parallel Sub-LM Calls)

Use this as a ready template for `execute_repl_code` calls.

## Step 1 — Inspect memory keys and build source text

```repl
import re
import json

TARGET_FILES = [k for k in memory_context.keys() if k.endswith('.md') or k.endswith('.jsonl')]
print('target files:', len(TARGET_FILES))

source_parts = []
for key in TARGET_FILES:
    text = memory_context.get(key, '')
    if text:
        source_parts.append(f"FILE: {key}\n{text}")

source_text = "\n\n".join(source_parts)
print('source chars:', len(source_text))
```

## Step 2 — Chunk text safely for local model

```repl
MAX_CHARS = 12000
OVERLAP = 400

chunks = []
start = 0
while start < len(source_text):
    end = min(start + MAX_CHARS, len(source_text))
    chunks.append(source_text[start:end])
    if end == len(source_text):
        break
    start = end - OVERLAP

print('chunks:', len(chunks))
```

## Step 3 — Build strict extraction prompts and run in parallel

```repl
instruction = (
    "Извлеки только факты в формате JSON-массива объектов с полями "
    "{type, entity, date, value, source}. "
    "Если совпадений нет, верни [] и ничего больше."
)

prompts = [
    f"{instruction}\n\nТекст для анализа:\n{chunk}"
    for chunk in chunks
]

raw_answers = llm_query_many(prompts, max_concurrency=6)
print('answers:', len(raw_answers))
```

## Step 4 — Normalize, deduplicate, and finalize

```repl
def parse_json_array(text: str):
    text = text.strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, list) else []
    except Exception:
        return []

rows = []
for answer in raw_answers:
    rows.extend(parse_json_array(answer))

seen = set()
deduped = []
for row in rows:
    key = json.dumps(row, ensure_ascii=False, sort_keys=True)
    if key not in seen:
        seen.add(key)
        deduped.append(row)

final_answer = json.dumps(deduped, ensure_ascii=False, indent=2)
FINAL_VAR('final_answer')
```

## Optional Step 5 — Persist to memory log

```repl
from datetime import datetime, timezone

ts = datetime.now(timezone.utc).isoformat()
out_path = 'memory/logs/extracted_facts.jsonl'

import os
os.makedirs('memory/logs', exist_ok=True)

with open(out_path, 'a', encoding='utf-8') as f:
    for row in deduped:
        event = {
            'ts': ts,
            'type': 'extracted_fact',
            'value': row,
        }
        f.write(json.dumps(event, ensure_ascii=False) + '\n')

print('saved:', len(deduped), '->', out_path)
```

---

## Notes

- Keep prompts deterministic and narrow (Sub-LM as extractor, not planner).
- Tune `MAX_CHARS` between 10k-15k depending on your local model context budget.
- Use `reload_memory_context()` after writing files if you need fresh content in REPL globals.
