# Spec: Light Themes — "White Gallery" & "Marble Foyer"
> Date: 2026-02-28
> Origin: /anchor_plan

## Recommended Model
**Target**: Claude Opus / Sonnet
**Reason**: Массивная CSS-работа (~120 правил), нужен точный парсинг длинного base.html (3096 строк)

---

## Objective
Добавить две светлые темы к существующим двум тёмным (Cyber Velvet, Emerald Prestige):
1. **"White Gallery"** (gallery) — холодная минималистичная светлая тема в стиле Apple/Берлинской галереи
2. **"Marble Foyer"** (marble) — тёплая премиальная светлая тема в стиле Old Money / гербовой бумаги

Переключение через настройки пользователя, сохранение в БД, мгновенное применение без перезагрузки.

---

## Architecture & Context

- **Текущая система**: `data-theme` атрибут на `<html>`, CSS-переменные в `:root` + `[data-theme="emerald"]`
- **Модель**: `User.theme` — `CharField(max_length=10)` с choices `('velvet', 'emerald')`
- **Context processor**: `core/context_processors.py` → `user_theme()` → `{{ user_theme }}`
- **Переключатель**: `templates/users/settings.html` — JS `switchTheme()` + AJAX POST
- **Backend**: `users/views.py:800` — валидация `theme in ('velvet', 'emerald')`, save
- **CSS**: `templates/base.html` (3096 строк) — ~75 hardcoded dark правил
- **Доп. CSS**: `static/css/adaptive.css` (~8), `animations.css` (~8), `mobile.css` (~29)

### Relevant ADRs / Docs:
- `LightThemes.md` — полные палитры и типографика для обеих тем
- `Scripts/theme_definitions.md` — справочная карта текущих тем
- `designUpdate.md` — дизайн-решения Digital Velvet

---

## Color Palettes (из LightThemes.md)

### Gallery (Белая Галерея)
| Token | Value | Описание |
|-------|-------|----------|
| bg-deep (canvas) | `#F4F4F9` | Gallery Grey — холодный синеватый фон |
| bg-card | `#FFFFFF` | Чисто белые карточки |
| bg-glass | `rgba(0, 0, 0, 0.02)` | Лёгкий glass-overlay |
| border-glass | `rgba(0, 0, 0, 0.06)` | Мягкие borders |
| text-main | `#13131A` | Deep Space — почти чёрный с синим |
| text-dim | `#6B6B78` | Приглушённый |
| text-heading | `#13131A` | Заголовки |
| CTA | `#007BFF` | Azure Ink — насыщенный лазурный |
| CTA hover | `#0062CC` | Темнее при наведении |
| CTA glow | `rgba(0, 123, 255, 0.12)` | Мягкая тень вместо glow |
| accent-secondary | `#5A2E98` | Royal Violet — аметистовый |
| crimson | `#BE123C` | Приглушённый розово-красный |
| gold | `#D4A017` | Плотное тёплое золото |
| Heading font | Onest | Современный геометрический |
| Body font | Inter (weight 500) | Плотнее на светлом фоне |
| Mono font | JetBrains Mono | Технические данные |

### Marble (Мраморное Фойе)
| Token | Value | Описание |
|-------|-------|----------|
| bg-deep (canvas) | `#FAF9F5` | Carrara Marble — тёплая слоновая кость |
| bg-card | `#FDFDFC` | Почти белый тёплый |
| bg-glass | `rgba(0, 0, 0, 0.015)` | Едва заметный |
| border-glass | `rgba(0, 0, 0, 0.05)` | Минимальные borders |
| text-main | `#2A2724` | Espresso Black — шоколадный |
| text-dim | `#6D6560` | Тёплый приглушённый |
| text-heading | `#1B2420` | Forest Onyx — с зелёным отливом |
| CTA | `#046C4E` | Heritage Emerald — британский гоночный зелёный |
| CTA hover | `#035C42` | Темнее |
| CTA glow | `rgba(4, 108, 78, 0.12)` | Мягкая тень |
| gold | `#C59B27` | Burnished Gold — бронзовая латунь |
| crimson | `#BE123C` | Hint of Ruby |
| Heading font | Playfair Display | Классика, высокий контраст |
| Body font | Commissioner | Гуманистический гротеск |
| Mono font | JetBrains Mono | Технические данные |

---

## Proposed Changes

### Phase 1: Backend — Модель и API (5 мин)

- [ ] **1.1** `users/models.py` — расширить `THEME_CHOICES`:
  ```python
  THEME_CHOICES = (
      ('velvet', _('Cyber Velvet')),
      ('emerald', _('Emerald Prestige')),
      ('gallery', _('White Gallery')),
      ('marble', _('Marble Foyer')),
  )
  theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='velvet', ...)
  ```

- [ ] **1.2** `users/views.py:802` — обновить валидацию:
  ```python
  if theme in ('velvet', 'emerald', 'gallery', 'marble'):
  ```

- [ ] **1.3** Создать миграцию:
  ```powershell
  .\venv\Scripts\python.exe manage.py makemigrations users
  .\venv\Scripts\python.exe manage.py migrate
  ```

### Phase 2: Шрифты (2 мин)

- [ ] **2.1** `templates/base.html` — добавить Google Fonts link:
  ```html
  <!-- Light theme fonts: Gallery + Marble -->
  <link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700;800&family=Playfair+Display:wght@400;500;600;700&family=Commissioner:wght@400;500;600;700&display=swap" rel="stylesheet">
  ```

### Phase 3: CSS-переменные — `[data-theme="gallery"]` и `[data-theme="marble"]` (20 мин)

Основной блок. Добавить после существующего `[data-theme="emerald"]` блока в `<style>` в `base.html`.

- [ ] **3.1** Блок `[data-theme="gallery"]` — переопределение ВСЕХ CSS-переменных из `:root`:
  - Все `--bg-*`, `--text-*`, `--border-*`, `--shadow-*`, `--glass-*`, `--nav-bg*`, `--scroll-*`
  - `--font-head: 'Onest', sans-serif`
  - `--cta` / `--cta-glow` / `--cta-hover` → Azure Ink palette
  - `--body-bg` / `--html-bg` → `#F4F4F9`
  - `color-scheme: light`

- [ ] **3.2** Блок `[data-theme="marble"]` — аналогично:
  - Все тёплые тона `--bg-*`: `#FAF9F5`, `#FDFDFC`
  - `--font-head: 'Playfair Display', serif`
  - `--font-body: 'Commissioner', sans-serif`
  - `--cta` → Heritage Emerald palette

- [ ] **3.3** Переопределения hardcoded стилей. Каждая из двух тем нужно объединить через selector list, ниже пример:

  ```css
  /* ═══ LIGHT THEMES: shared overrides ═══ */
  [data-theme="gallery"],
  [data-theme="marble"] {
      color-scheme: light;
  }
  
  [data-theme="gallery"] body,
  [data-theme="marble"] body {
      background: var(--body-bg);
      color: var(--text-main);
  }
  ```
  
  **Группы переопределений (в один CSS-блок):**
  
  | Группа | Что менять | Примеров |
  |--------|-----------|--------|
  | body background | `radial-gradient(...)` → solid `var(--body-bg)` | 2 |
  | `.glass-card` | bg, border, hover border, hover glow → shadow | 4 |
  | `.navbar` | bg opacity → `rgba(244,244,249,0.92)` / `rgba(250,249,245,0.92)` | 2 |
  | `.dropdown-menu` | bg → white/ivory, border → subtle | 2 |
  | `.modal-content` | bg → white/ivory, shadow → soft | 4 |
  | `.form-control`, `.form-select` | bg → transparent/subtle, text → dark, border → light | 6 |
  | `.btn-primary` | glow → soft shadow | 3 |
  | `.text-secondary`, `.text-muted` | → `var(--text-dim)` | 2 |
  | `.form-label`, `label` | color → `var(--text-main)` | 2 |
  | `.table` styles | text, bg, hover → light variants | 5 |
  | `.premium-limit-modal` | bg → white/ivory | 3 |
  | footer | bg, text → dark on light | 5 |
  | scrollbar | track/thumb → light greys | 3 |
  | glow blobs | opacity → 0 или пастельные | 2 |
  | `.glass-toast` | bg → white with shadow | 2 |
  | cookies banner | bg → light | 1 |
  
  **Итого ~47 правил в объединённом блоке** + ~6 правил для различий между gallery и marble.

### Phase 4: Доп. CSS файлы (10 мин)

- [ ] **4.1** `static/css/mobile.css` — добавить блоки `[data-theme="gallery"]`, `[data-theme="marble"]`:
  - `.mobile-sidebar` bg → light
  - `.mob-notif-panel` bg → light
  - `.mob-nav-item` и badges → dark text on light bg
  - `.mob-profile-name` → dark text
  - ~15 правил

- [ ] **4.2** `static/css/adaptive.css` — минимальные переопределения:
  - glow-blob скрытие
  - button colors
  - ~5 правил

- [ ] **4.3** `static/css/animations.css` — glow → shadow:
  - `.glass-glow` → мягкие тени
  - `@keyframes glow-pulse` → subtle pulse
  - ~4 правила

### Phase 5: Settings UI — карточки тем (15 мин)

- [ ] **5.1** `templates/users/settings.html` — добавить 2 новых карточки в `#themeSwitcher`:
  
  **Карточка "White Gallery":**
  - Светлый preview (`bg: #F4F4F9`, линии: `#007BFF`, `rgba(0,0,0,0.1)`, `rgba(0,0,0,0.05)`)
  - Swatches: `#007BFF`, `#5A2E98`, `#BE123C`, `#D4A017`
  - Описание: `{% trans "Стерильный, минималистичный, галерейный" %}`

  **Карточка "Marble Foyer":**
  - Тёплый preview (`bg: #FAF9F5`, линии: `#046C4E`, `rgba(0,0,0,0.08)`, `rgba(0,0,0,0.04)`)
  - Swatches: `#046C4E`, `#C59B27`, `#BE123C`, `#1B2420`
  - Описание: `{% trans "Премиальный, классический, статусный" %}`

- [ ] **5.2** CSS для светлых preview карточек (`.theme-card__preview--gallery`, `.theme-card__preview--marble`)

- [ ] **5.3** Обновить CSS карточек тем: в light-теме карточки тем должны сохранять контрастность (тёмные карточки на светлом фоне настроек)

### Phase 6: meta theme-color (2 мин)

- [ ] **6.1** `templates/base.html` — динамический `theme-color`:
  ```html
  <meta name="theme-color" content="{% if user_theme == 'gallery' %}#F4F4F9{% elif user_theme == 'marble' %}#FAF9F5{% else %}#000000{% endif %}">
  ```

- [ ] **6.2** JS в `switchTheme()` — обновлять `meta[name='theme-color']` мгновенно

### Phase 7: i18n (3 мин)

- [ ] **7.1** Все новые строки обернуть в `{% trans %}` / `_()` 
- [ ] **7.2** Запустить `compile_mo.py` для обновления locales

### Phase 8: Cache busting (1 мин)

- [ ] **8.1** Обновить `?v=` на ВСЕХ изменённых CSS файлах в base.html

---

## 3 Железных Правила для Light-тем (Архитектура UI)

1. **Тени вместо свечения** — в light-темах `box-shadow` с `rgba(0,0,0,0.05-0.15)` вместо neon glow
   ```css
   box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
   ```
2. **Обводки минимизированы** — разделение через пространство и разницу фона, не линиями
3. **Font-weight +1 шаг** — базовый текст `500` вместо `400` для Gallery

---

## Файлы, затронутые изменениями

| Файл | Изменения |
|------|-----------|
| `users/models.py` | +2 choices в THEME_CHOICES |
| `users/views.py` | +2 значения в валидации |
| `users/migrations/0027_*.py` | Автогенерация |
| `templates/base.html` | +Google Fonts, +CSS ~60 правил, meta theme-color |
| `templates/users/settings.html` | +2 theme cards, +CSS для previews |
| `static/css/mobile.css` | +~15 правил |
| `static/css/adaptive.css` | +~5 правил |
| `static/css/animations.css` | +~4 правила |

---

## Что НЕ трогаем (scope exclusion)

- Мобильное приложение (Capacitor) — у него своя тема через `prefers-color-scheme`, отдельная задача
- Email шаблоны — остаются dark
- Admin views — остаются default Django admin

---

## Estimated Scope

| Метрика | Значение |
|---------|----------|
| Файлов затронуто | 8 |
| CSS правил добавить | ~85 |
| Строк кода (прибл.) | ~350–450 |
| Оценка сложности | **Large** |
| Время реализации | ~45–60 мин |

---

## Verification & Tests

- [ ] `.\venv\Scripts\python.exe manage.py check` — без ошибок
- [ ] `.\venv\Scripts\python.exe manage.py migrate` — миграция применена
- [ ] Переключить тему на "gallery" в настройках → мгновенно светлая тема
- [ ] Переключить тему на "marble" → тёплая светлая тема
- [ ] Вернуться на "velvet" / "emerald" → тёмные темы работают
- [ ] Проверить: navbar, cards, modals, forms, footer, scrollbar, tables
- [ ] Mobile: sidebar, notification panel, nav bar — адаптивность
- [ ] Cookie banner — корректные цвета в light
- [ ] F5 — тема сохраняется между перезагрузками
- [ ] WCAG: контраст текст/фон ≥ 4.5:1

---

## Порядок имплементации (рекомендация)

1. Backend (Phase 1) — база, чтобы тема сохранялась
2. Шрифты (Phase 2) — preload
3. CSS variables (Phase 3.1, 3.2) — переменные = основа
4. Hardcoded overrides (Phase 3.3) — покрытие base.html
5. Settings UI (Phase 5) — карточки для выбора
6. Доп. CSS (Phase 4) — mobile, adaptive, animations
7. Meta + cache bust (Phase 6, 8)
8. i18n (Phase 7)
9. Тестирование (Verification)
