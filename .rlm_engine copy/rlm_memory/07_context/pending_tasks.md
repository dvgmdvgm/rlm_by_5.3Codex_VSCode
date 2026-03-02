# Pending Tasks

> **Updated**: 2026-03-01 00:35

---

## High Priority

| Task | Description | Date Added |
|------|-------------|------------|
| Emerald визуальная проверка + коммит | 56 файлов с заменой hardcoded цветов на CSS vars — ожидает визуальной проверки и git commit/push | 2026-02-28 |
| Firebase Server Key | Replace `firebase-service-account.json` with key from project `artconnect-95afc`. Manual: Firebase Console -> Project Settings -> Service Accounts -> Generate New Private Key. Without this, push notifications will NOT work. | 2026-02-27 |

---

## Medium Priority

| Task | Description | Date Added |
|------|-------------|------------|
| Review notification routing + auto-read | Спек готов: `specs/review-notification-routing-and-autoread.md`. Backend `action: 'leave_review'` + mobile routing + auto-mark read | 2026-02-28 |
| Mobile i18n | Internationalization of the mobile app (~200 hardcoded strings, 25+ files). Plan mapped in `12_roadmap/mobile_i18n_plan.md`. Waiting for all screens to be finalized. | 2026-02-27 |
| Cleanup WorldMapModal | Delete unused `WorldMapModal.jsx` and `WorldMapModal.css` (replaced by GeographyScreen) | 2026-02-28 |
| Cleanup temp files | Удалить `__emerald_diff_templates.txt`, `_analyze_context.py`, `_analyze_diff.py` из корня проекта | 2026-02-28 |

---

## Low Priority

| Task | Description | Date Added |
|------|-------------|------------|
| Zoho Mail Inbox | Configure Zoho Mail Free for `info@scenica.online` (reading/replying) | 2026-02-23 |

---

## Recently Completed

| Task | Completed | Date |
|------|-----------|------|
| **Emerald theme CSS vars интеграция** | 253 замены hardcoded цветов в 53 файлах, Python скрипт, CSS vars для всех 4 тем | 2026-02-28 |
| **Light themes (Gallery + Marble)** | Backend + CSS + settings UI для двух светлых тем | 2026-02-28 |
| **Empty-state breathing animation** | Unified breathing/pulsating animation, 8 файлов | 2026-02-28 |
| **Git push + emerald stash recovery** | Push main (36d0788), branch emerald-theme (0102924) на GitHub | 2026-02-28 |
| **Geography nav/status/back fixes (mobile)** | Исправлены TopBar `onBack`, hardware back fallback и краш jsvectormap (`selector undefined`) через ADB-диагностику | 2026-02-28 |
| **GeographyScreen (mobile)** | Карта мира с visited countries — endpoint + экран `/geography/:id?` | 2026-02-28 |
| **Dashboard widget redesign** | Streak banner clickable, stat card -> мои отклики | 2026-02-27 |
| **Settings split** | Настройки профиля + Настройки приложения (AppSettingsScreen) | 2026-02-27 |
| **YouTube inline player** | ArtistDetailScreen: iframe embed instead of external link | 2026-02-27 |
| **GamificationScreen checkmark** | Checkmark badge on current level | 2026-02-27 |
| **Artist ApplicationsScreen redesign** | Status filter tabs, improved cards, smart nav to contract/job | 2026-02-27 |
| **Catalog hides applied jobs** | `has_applied` filtering in JobsScreen | 2026-02-27 |
| **Review system fixes (web+mobile)** | artist URL, leave_review redirect, ActionPicker navigation | 2026-02-27 |
| **ModalOverlay universal wrapper** | All 6 modals refactored to use ModalOverlay + useBackClose | 2026-02-27 |
| **UnboundLocalError `_` fix** | `streak, _` → `streak, _created` in users/views.py | 2026-02-27 |
| **DB cleanup: jobs without end date** | Deleted 22 jobs with null contract_end_date | 2026-02-27 |
| **Push Notification channel_id Fix** | channel_id mismatch fixed: scenica_default → artconnect_default | 2026-02-27 |
| **Mobile Review System** | LeaveReviewScreen + backend has_employer_review + dashboard navigation | 2026-02-27 |
| **Rear Camera Default** | @capacitor/camera plugin for rear camera in DocumentUploader | 2026-02-27 |
| **Digital Velvet Font System** | Unbounded+Inter+Fira Code. 11 files updated | 2026-02-27 |
| **Adaptive `create_job.html`** | Container Queries, Fluid Typography, Logical Properties, CSS Grid | 2026-02-27 |
| **FOMO view_count tracking** | Proper viewer counts initialized for FOMO metrics (web + mobile) | 2026-02-26 |
| **get_display_name() refactor** | Enforced `company_name` for employers across 22+ locations (models, views, serializers, templates, React) | 2026-02-26 |
| **build_and_install.bat** | Built local automation script: Vite build → Cap sync → Gradle build → ADB install | 2026-02-26 |
| **Push navigation cold-start fix** | 2-phase push init: global tap listeners in App + navigateOrQueue buffer setup | 2026-02-26 |
| **Disabled global mobile haptics** | All haptic functions converted to no-ops to comply with strict design rules | 2026-02-26 |
| **Root file audit** | 17 temporary/build files flagged (~249 MB) for cleanup phase | 2026-02-26 |
