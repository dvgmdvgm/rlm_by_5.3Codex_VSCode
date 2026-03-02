# Spec: Empty State — Breathing/Pulsating Animation
> Date: 2026-02-28
> Origin: /anchor_plan

## Objective
Применить единую "дышащую" пульсирующую анимацию иконки на ВСЕХ экранах, где отображается пустое состояние (empty state). Сейчас анимация `emptyBobble` работает только на `.empty-state__icon`, но не все экраны используют эту обёртку, и некоторые используют свои классы (`dash-empty`, `dash-map__empty`, `geo-screen__empty`).

## Architecture & Context
- **Root Directory**: `artconnect-mobile/app/src/`
- **Main CSS**: `styles/theme.css` (строки 437-439 — `.empty-state`, строки 1103-1113 — `emptyBobble`)
- **Dashboard CSS**: `screens/Dashboard.css` (строки 515-530 — `.dash-empty`)
- **Geography CSS**: `screens/GeographyScreen.css` (строки 47-57 — `.geo-screen__empty`)

## Audit: All Empty State Locations

### Group A — Уже используют `.empty-state__icon` (анимация `emptyBobble` работает):
| # | File | Icon | Line |
|---|------|------|------|
| 1 | CatalogScreen.jsx | `palette` | 223 |
| 2 | JobsScreen.jsx | `briefcase` | 240 |
| 3 | MessagesScreen.jsx | `message` | 53 |
| 4 | NotificationsScreen.jsx | `bell` | 151 |
| 5 | ReviewsScreen.jsx | `star` | 160, 165 |
| 6 | ApplicationsScreen.jsx | `clipboard` | 114, 140 |
| 7 | JobApplicationsScreen.jsx | `users` | 336 |
| 8 | ArtistDetailScreen.jsx | `frown` | 130 |
| 9 | EmployerDetailScreen.jsx | `frown` | 102 |
| 10 | JobDetailScreen.jsx | `alertTriangle` | 72 |

### Group B — Используют `.empty-state`, но БЕЗ обёртки `.empty-state__icon` (Icon рендерится напрямую):
| # | File | Icon | Line |
|---|------|------|------|
| 1 | GamificationScreen.jsx | `alertTriangle` | 86 |
| 2 | StreakScreen.jsx | `alertTriangle` | 66 |
| 3 | FomoScreen.jsx | `alertTriangle` | 39 |
| 4 | MyJobsScreen.jsx | `briefcase` | 94 |
| 5 | MyContractsScreen.jsx | `fileText` | 98 |

### Group C — Используют другие CSS-классы (`dash-empty`, `dash-map__empty`, `geo-screen__empty`):
| # | File | Class | Icon | Line |
|---|------|-------|------|------|
| 1 | ArtistDashboard.jsx | `dash-empty` | `clipboard` | 298-299 |
| 2 | EmployerDashboard.jsx | `dash-empty` | `users` | 236 |
| 3 | HomeScreen.jsx | `dash-empty` | `alertTriangle` | 77 |
| 4 | ArtistDashboard.jsx | `dash-map__empty` | `globe` | 333 |
| 5 | GeographyScreen.jsx | `geo-screen__empty` | `globe` | 113 |

## Proposed Changes

### 1. CSS: Улучшить анимацию `emptyBobble` → `emptyBreathing` (theme.css)
Заменить текущую `emptyBobble` на более выразительную "дышащую" анимацию с плавным масштабированием + лёгким покачиванием + мягким glow:

```css
/* --- EMPTY STATE breathing animation --- */
.empty-state__icon {
  animation: emptyBreathing 3.5s ease-in-out infinite;
  will-change: transform, opacity;
}
@keyframes emptyBreathing {
  0%, 100% {
    transform: scale(1) translateY(0);
    opacity: 0.5;
    filter: drop-shadow(0 0 0 transparent);
  }
  50% {
    transform: scale(1.08) translateY(-6px);
    opacity: 0.75;
    filter: drop-shadow(0 4px 12px rgba(37, 99, 235, 0.15));
  }
}
```

### 2. JSX Group B: Обернуть Icon в `<div className="empty-state__icon">` (5 файлов)

- [x] **GamificationScreen.jsx** (строка ~86): обернуть `<Icon name="alertTriangle" .../>` в `<div className="empty-state__icon">...</div>`
- [x] **StreakScreen.jsx** (строка ~66): аналогично
- [x] **FomoScreen.jsx** (строка ~39): аналогично
- [x] **MyJobsScreen.jsx** (строка ~94): обернуть `<Icon name="briefcase" .../>` в `<div className="empty-state__icon">...</div>`
- [x] **MyContractsScreen.jsx** (строка ~98): обернуть `<Icon name="fileText" .../>` в `<div className="empty-state__icon">...</div>`

### 3. CSS Group C: Добавить анимацию для `dash-empty`, `dash-map__empty`, `geo-screen__empty`

В **Dashboard.css** — добавить анимацию иконкам внутри `dash-empty` и `dash-map__empty`:
```css
.dash-empty > svg,
.dash-empty > .dash-empty__icon,
.dash-map__empty > svg {
  animation: emptyBreathing 3.5s ease-in-out infinite;
  will-change: transform, opacity;
}
```

В **GeographyScreen.css** — добавить анимацию иконке внутри `geo-screen__empty`:
```css
.geo-screen__empty > svg {
  animation: emptyBreathing 3.5s ease-in-out infinite;
  will-change: transform, opacity;
}
```

Так как `@keyframes emptyBreathing` определена в `theme.css` (глобально), она доступна из любого CSS-файла.

### 4. Не трогать: HomeScreen `dash-empty` (ошибка)
HomeScreen использует `dash-empty` для ошибки загрузки — анимация туда тоже попадёт через CSS Group C, что уместно.

## Verification & Tests
- [x] Запустить `vite build` — сборка прошла успешно
- [ ] Визуально проверить на устройстве/эмуляторе

## Implementation Status: COMPLETED
- **Size**: Small-Medium
- **Files modified**: 8 (1 CSS theme + 2 CSS component + 5 JSX)
- **Risk**: Minimal — чисто визуальные изменения, CSS-only анимация
