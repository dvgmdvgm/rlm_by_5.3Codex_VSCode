# Mobile App i18n — Internationalization Plan

> **Status**: DEFERRED (Pending finalization of all mobile application screens)  
> **Priority**: Medium  
> **Created**: 2026-02-27  
> **Technology**: React + Capacitor (Vite)
> **Modified**: 2026-02-27 (Translated to EN)

---

## 1. Current State

The mobile application is **fully hardcoded in Russian**:
- **~200+** Russian strings in JSX files (titles, placeholders, labels, textual content).
- **15** instances of `toLocaleDateString('ru')` / `toLocaleString('ru')` — dates are formatted only in Russian.
- **0** i18n infrastructure (no libraries, no translation files, no language context).

Note: Django `.po`/`.mo` files are NOT used by the mobile application; these are separate systems.

---

## 2. Audit: Files with Hardcoded Strings

### Screens (screens/) — Russian strings
| File | Examples of Strings | Avg. Count |
|------|--------------------|------------|
| `JobsScreen.jsx` | "Jobs", "Search jobs...", "All genres", "Reset", "Flight", "Visa", "Accommodation", "Urgent only" | ~15 |
| `JobDetailScreen.jsx` | "Job", "Conditions", "Description", "Your application", "Cover letter", "Urgent" | ~10 |
| `CatalogScreen.jsx` | "Artist Catalog", "Search by name...", "All genres", "Gender", "Schengen Visa" | ~12 |
| `CreateJobScreen.jsx` | "New Job", "Job Title", "Genre", "Country", "City", "Salary", "Description", "Conditions", "Urgent" | ~15 |
| `ProfileScreen.jsx` | "Profile", "Rating", "Reviews", "Profile Completion", "Settings", "Catalog", "Jobs", "Hired" | ~12 |
| `SettingsScreen.jsx` | "Settings", "Personal Data", "First Name", "Last Name", "Language", "Account", "Role" | ~10 |
| `ArtistDetailScreen.jsx` | "Artist", "Rating", "Reviews", "Profile", "Tags", "No reviews yet" | ~8 |
| `EmployerDetailScreen.jsx` | "Employer", "Jobs", "Contracts", "Rating", "Badges", "Tags", "Urgent" | ~12 |
| `ArtistDashboard.jsx` | "day streak", "views", "Find Work", "My Applications", "Messages", "No applications yet" | ~8 |
| `EmployerDashboard.jsx` | "jobs", "contracts", "Create Job", "Artist Catalog", "Applications" | ~8 |
| `MessagesScreen.jsx` | "Messages", "No messages" | 2 |
| `ChatScreen.jsx` | "Message..." | 1 |
| `NotificationsScreen.jsx` | "Notifications", "No notifications" | 2 |
| `ReviewsScreen.jsx` | "Reviews", "You have no reviews yet", "stars" | 3 |
| `ContractViewScreen.jsx` | "Contract", "Download" | 4 |
| `GamificationScreen.jsx` | "Level & Achievements", "Failed to load data" | 2 |
| `StreakScreen.jsx` | "Login Streak", "Current Streak", "Record" | 4 |
| `FomoScreen.jsx` | "Profile Views", "No views this week" | 3 |
| `MyJobsScreen.jsx` | "My Jobs", "Active", "Closed", "Total", "Create Job", "Urgent" | 6 |
| `MyContractsScreen.jsx` | "My Contracts", "Signed", "Waiting for Signature", "Total" | 4 |
| `UrgentPaymentScreen.jsx` | "Payment", "Urgent Promotion", "Card Number", "Expiry", "Payment Successful!" | 6 |
| `LoginScreen.jsx` | "Username", "Password" | 2 |
| `JobApplicationsScreen.jsx` | "Rating", "Height", "Weight", "Reviews", "Cover Letter" | 5 |

### Components (components/)
| File | Examples | Avg. Count |
|------|----------|------------|
| `TabBar.jsx` | "Create Job" (aria-label) | 1 |
| `SignaturePad.jsx` | "Please sign here" | 1 |
| `DocumentUploader.jsx` | "Upload Document", "Take Photo", "Select File", "Cancel" | 4 |

### Hardcoded Date Formatting ('ru') (15 locations)
| File | Lines |
|------|-------|
| `ApplicationsScreen.jsx` | L140 |
| `ArtistDetailScreen.jsx` | L250, L301 |
| `NotificationsScreen.jsx` | L157 |
| `SettingsScreen.jsx` | L135 |
| `ReviewsScreen.jsx` | L189 |
| `JobApplicationsScreen.jsx` | L122 |
| `EmployerDetailScreen.jsx` | L283 |
| `ContractViewScreen.jsx` | L390 (×2), L495, L537 |
| `StreakScreen.jsx` | L50 |
| `FomoScreen.jsx` | L101 |

---

## 3. Recommended Stack

```
react-i18next + i18next          — Core i18n library
i18next-browser-languagedetector — Automatic device language detection
```

---

## 4. Proposed Architecture

### 4.1. Translation File Structure
```
app/src/
  locales/
    ru.json      ← Russian (Base language)
    en.json      ← English
    es.json      ← Spanish (etc.)
  i18n.js        ← i18next Configuration
```

### 4.2. Sample JSON Format
```json
{
  "nav": {
    "jobs": "Jobs",
    "messages": "Messages",
    "notifications": "Notifications",
    "profile": "Profile"
  },
  "jobs": {
    "title": "Jobs",
    "search": "Search jobs...",
    "allGenres": "All genres",
    "reset": "Reset",
    "urgent": "Urgent",
    "noJobs": "No jobs found",
    "conditions": "Conditions",
    "flight": "Flight",
    "visa": "Visa",
    "accommodation": "Accommodation"
  },
  "common": {
    "rating": "Rating",
    "reviews": "Reviews",
    "tags": "Tags",
    "loading": "Loading...",
    "error": "Failed to load data",
    "cancel": "Cancel"
  }
}
```

### 4.3. i18n.js Configuration Template
```js
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import ru from './locales/ru.json';
import en from './locales/en.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { ru: { translation: ru }, en: { translation: en } },
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    }
  });

export default i18n;
```

---

## 5. Execution Order (Checklist)

- [ ] Install dependencies: `react-i18next`, `i18next`, `i18next-browser-languagedetector`
- [ ] Initialize `app/src/i18n.js`
- [ ] Extract all Russian strings into `app/src/locales/ru.json` (~200+ keys)
- [ ] Create `app/src/locales/en.json` (English translation)
- [ ] Import `import './i18n'` in `main.jsx`
- [ ] Replace hardcoded strings with `t('key')` across all 25+ files
- [ ] Replace the hardcoded `'ru'` locale in date formatting with `i18n.language` in 15 locations
- [ ] Update `SettingsScreen.jsx` to allow language switching via `i18n.changeLanguage()`
- [ ] (Optional) Develop `po_to_json.py` to synchronize with Django web translations

---

## 6. Effort Estimation

| Phase | Estimated Time |
|-------|----------------|
| Infrastructure setup | ~15 min |
| String extraction to ru.json | ~1 hour |
| Code replacement in 25+ files | ~2 hours |
| English translation (en.json) | ~30 min |
| Testing & Verification | ~30 min |
| **Total** | **~4.5 hours** |
