# 📍 Инструкции для агента — Scenica

> **Импортировано из**: `PROJECT_CONTEXT.md`, `GEMINI.md`
> **Дата**: 2026-02-06

---

## Общие правила

1. **Не использовать emojis** в качестве иконок — только Bootstrap Icons или SVG
2. **Cursor Pointer** — всегда добавлять `cursor: pointer` кликабельным элементам
3. **Transitions** — использовать плавные переходы 200-300ms для всех hover-эффектов

---

## После изменения HTML-файлов

**ОБЯЗАТЕЛЬНО** выполнить скрипт `fix_django_templates.py` из папки `Scripts`:

```bash
# Сначала dry-run для проверки
python Scripts/fix_django_templates.py --dry-run

# Потом применить изменения
python Scripts/fix_django_templates.py
```

---

## Известные проблемы (Tech Debt)

| Проблема | Файл | Статус |
|----------|------|--------|
| Линтинг CSS inline styles | `base.html:517` | Ожидает |
| Линтинг JS запятые | `my_applications.html` | Ожидает |
| Service Worker offline | - | Требует настройки |

---

## Ключевые файлы

| Файл | Назначение |
|------|------------|
| `templates/base.html` | Главный layout (72KB — будь осторожен!) |
| `PROJECT_CONTEXT.md` | Полный контекст проекта |
| `design_proposal.md` | Референс дизайн-системы |
| `GEMINI.md` | Критические правила UI |
| `Идеи.md` | Бизнес-модель и roadmap |
