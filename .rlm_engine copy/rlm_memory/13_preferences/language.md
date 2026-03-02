# 🧠 LANGUAGE SETTING / НАСТРОЙКА ЯЗЫКА

> **Date**: 2026-02-27
> **Logic**: DUAL-LANGUAGE (Storage: EN, Communication: USER_PREF)

---

## ⚙️ Core Configuration

This setting controls the language for **AI communication** and **Storage**. 

```yaml
# COMMUNICATION_LANGUAGE: The language the AI uses to talk to the user.
# Referenced from this file or language_local.md.
COMMUNICATION_LANGUAGE: ru

# STORAGE_LANGUAGE: The language used for ALL files in .agent/memory/.
# This is hardcoded to 'en' to optimize token usage.
STORAGE_LANGUAGE: en
```

---

## 📜 Dual-Language Logic (CRITICAL)

To optimize token usage and ensure maximum AI performance:

1.  **Read/Write (Storage)**:
    - **ALL** Markdown files in `.agent/memory/` MUST be written and updated in **English** (`en`).
    - Decisions, logs, summaries, and technical notes are stored in English regardless of the communication language.
    - AI should think in English when processing memory.

2.  **Talk (Communication)**:
    - AI must respond to the user in the language specified in `COMMUNICATION_LANGUAGE` (e.g., Russian).
    - Code explanations, summaries in the chat, and general conversation happen in the user's preferred language.

---

## 🌍 Supported Communication Languages

| Code | Language | Язык |
|------|----------|------|
| `en` | English | Английский |
| `ru` | Russian | Русский |
| `uk` | Ukrainian | Украинский |
| `es` | Spanish | Испанский |
| `de` | German | Немецкий |
| `fr` | French | Французский |
| `ja` | Japanese | Японский |
| `pt` | Portuguese | Португальский |
| `it` | Italian | Итальянский |
| `ko` | Korean | Корейский |
| `zh-CN` | Chinese (Simplified) | Китайский (Упр.) |

---

## 🔀 Local Override

If `language_local.md` exists, it overrides the `COMMUNICATION_LANGUAGE` defined here.
AI MUST check `language_local.md` FIRST.
