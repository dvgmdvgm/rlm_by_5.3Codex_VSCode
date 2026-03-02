# Restoring Emerald Proscenium Colors

- **Date**: 2026-02-27
- **Status**: Deferred (colors rolled back, project on original purple/blue)
- **Modified**: 2026-02-27 (Translated to EN)

---

## Current State

Project is at commit `ab09abf` — name **Scenica**, colors are **original** (purple/blue).

## How to Restore Emerald Colors

### Option 1: Via git stash (if stash is still available)

```powershell
git stash apply stash@{0}
```

If stash was removed from the list but reflog is still alive:

```powershell
git stash apply 5477206
```

Stash commit: `5477206` (name: "emerald-proscenium-color-changes")

### Option 2: Manual Application (if stash is lost)

Apply the design from `designUpdate.md` — the file contains the full specification for "The Emerald Proscenium".

**Replacement Palette:**

| Old Color | New Color | Purpose |
|-----------|-----------|---------|
| `#7c4dff`, `#6f42c1`, `#8b5cf6` | `#10B981` | Primary (Neo-Emerald) |
| `#a78bfa`, `#c4b5fd`, `#a855f7` | `#34D399` | Light emerald |
| `#6d28d9` | `#059669` | Dark emerald |
| `rgba(124, 77, 255, X)` | `rgba(16, 185, 129, X)` | Primary glow |
| `rgba(111, 66, 193, X)` | `rgba(16, 185, 129, X)` | Primary accent |
| `rgba(168, 85, 247, X)` | `rgba(52, 211, 153, X)` | Light glow |
| `rgba(139, 92, 246, X)` | `rgba(16, 185, 129, X)` | Secondary purple |
| `rgba(124, 58, 237, X)` | `rgba(16, 185, 129, X)` | Deep purple |

**Affected Files (~76 files, ~18 key files):**

- `static/css/mobile.css` — 5 replacements
- `static/css/animations.css` — 4 replacements
- `static/css/adaptive.css`
- `static/js/mobile_swipe.js` — 2 replacements
- `static/js/notifications.js`
- `templates/base.html` — CSS variables, Bootstrap overrides
- `templates/core/admin/dashboard.html`, `model_list.html`, `model_edit.html`
- `templates/core/conversation.html`
- `templates/core/includes/artists_table.html`
- `templates/jobs/my_jobs.html`, `my_applications.html`, `job_detail_content.html`, `dashboard.html`
- `templates/users/employer_public_content_v5.html`, `v4_tabs`, `V4`, `V3`, `V2`, `backup`
- `templates/users/artist_public_content.html`
- `templates/emails/welcome.html`, `visa_uploaded.html`, `verification_email.html`
- `core/templates/core/index.html`, `catalog.html`, `support.html`
- `artconnect-mobile/app/src/screens/ArtistDashboard.jsx`, `EmployerDashboard.jsx`, `GamificationScreen.jsx`
- `artconnect-mobile/app/src/styles/theme.css`
- `.bak` files (index.html.bak, job_detail_content_backup.html, dashboard.html.bak)

---

## Note

After restoring colors in the mobile source, a rebuild is required:
```powershell
cd artconnect-mobile; npm run build
```
