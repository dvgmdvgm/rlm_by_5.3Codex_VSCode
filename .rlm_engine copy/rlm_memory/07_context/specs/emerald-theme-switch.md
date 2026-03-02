# Spec: Emerald Proscenium — Bidirectional Theme Switch
> Date: 2026-02-28
> Origin: /anchor_plan

## Objective
Создать **двунаправленный скрипт переключения** между двумя дизайн-темами проекта:
- **Theme A** — "Digital Velvet" (текущий): синий CTA `#2563EB`, фиолетовые акценты `#7C3AED`, шрифты Unbounded / Inter / Fira Code
- **Theme B** — "Emerald Proscenium": изумрудный CTA `#10B981`, кармин `#E11D48`, шампань `#FBBF24`, шрифты Cormorant Garamond / Manrope / JetBrains Mono

Скрипт позволит переключаться `A → B` и `B → A` одной командой.

## Architecture & Context
- **Root Directory**: `d:\art_network_antigravity\`
- **Git stash**: Emerald stash commit `5477206` жив в reflog (69 файлов, 510 ins / 443 del)
- **Relevant ADR**: `.agent/memory/03_decisions/emerald_color_restore.md`
- **Design Doc**: `designUpdate.md`

## Current State Analysis

### Web Part (Django templates + static CSS)

#### CSS Variables (`:root` in base.html, line 58)
| Variable | Theme A (Digital Velvet) | Theme B (Emerald Proscenium) |
|----------|------------------------|------------------------------|
| `--bg-deep` | `#09090B` | `#0C0C0E` |
| `--bg-card` | `rgba(250,250,250,0.03)` | `#16161A` |
| `--primary` | `#18181B` | `#16161A` |
| `--primary-glow` | `rgba(24,24,27,0.4)` | `rgba(22,22,26,0.4)` |
| `--cta` | `#2563EB` | `#10B981` |
| `--cta-glow` | `rgba(37,99,235,0.4)` | `rgba(16,185,129,0.4)` |
| `--text-main` | `#E4E4E7` | `#F3F4F6` |
| `--text-dim` | `#A1A1AA` | `#9CA3AF` |
| `--text-heading` | `#FFFFFF` | `#FFFFFF` (same) |
| `--font-head` | `'Unbounded', sans-serif` | `'Cormorant Garamond', serif` |
| `--font-body` | `'Inter', system-ui, sans-serif` | `'Manrope', sans-serif` |
| `--font-mono` | `'Fira Code', monospace` | `'JetBrains Mono', monospace` |

**New variables in Theme B only:**
| Variable | Value | Purpose |
|----------|-------|---------|
| `--cta-hover` | `#059669` | Dark emerald for hover |
| `--crimson` | `#E11D48` | Theatrical accent (urgent, art) |
| `--crimson-glow` | `rgba(225,29,72,0.3)` | Crimson glow |
| `--gold` | `#FBBF24` | Ratings, VIP, status |
| `--gold-glow` | `rgba(251,191,36,0.3)` | Gold glow |

#### Google Fonts CDN (base.html, line ~42)
| Theme A | Theme B |
|---------|---------|
| `Archivo:wght@300;400;500;600;700;800` | `Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500` |
| `Space+Grotesk:wght@300;400;500;600;700` | `Manrope:wght@300;400;500;600;700;800` |
| *(none)* | `JetBrains+Mono:wght@400;500;600` |

**NOTE**: base.html currently loads `Archivo + Space Grotesk` as the CDN link, but `--font-head` is set to `Unbounded`. There is a legacy inconsistency — the actual rendering uses Unbounded/Inter from the mobile CSS override or browser cache. Theme B fixes this by aligning CDN with variables.

#### Legacy `:root` block (base.html, line ~1837)
This second block overrides `--accent-color: #7c4dff` and creates a gradient btn-primary. In Theme B, this block gets rewritten to Emerald values.

#### Hardcoded Colors (across ~60 template files)
The stash commit `5477206` already has the full diff for all 69 files. Key replacements:

| Old (Theme A) | New (Theme B) | Context |
|---------------|---------------|---------|
| `#2563EB` | `#10B981` | CTA buttons, links, borders |
| `#1D4ED8` | `#059669` | Hover/dark accent |
| `#7C3AED` / `#7c4dff` | `#10B981` | Purple accent → Emerald |
| `#a78bfa` / `#a855f7` | `#34D399` | Light purple → Light emerald |
| `#6d28d9` / `#6200ea` | `#059669` | Deep purple → Dark emerald |
| `rgba(37,99,235,X)` | `rgba(16,185,129,X)` | Blue glow → Emerald glow |
| `rgba(124,77,255,X)` | `rgba(16,185,129,X)` | Purple glow → Emerald glow |
| `rgba(139,92,246,X)` / `rgba(124,58,237,X)` | `rgba(16,185,129,X)` | Purple shades → Emerald |

### Mobile App (Capacitor / Vite)

#### theme.css CSS Variables
| Variable | Theme A | Theme B |
|----------|---------|---------|
| `--accent` | `#2563EB` | `#10B981` |
| `--accent-hover` | `#1D4ED8` | `#059669` |
| `--accent-light` | `rgba(37,99,235,0.15)` | `rgba(16,185,129,0.15)` |
| `--accent-gradient` | `linear-gradient(135deg,#2563EB 0%,#7C3AED 100%)` | `linear-gradient(135deg,#10B981 0%,#059669 100%)` |
| `--border-accent` | `rgba(37,99,235,0.3)` | `rgba(16,185,129,0.3)` |
| `--shadow-accent` | `0 4px 16px rgba(37,99,235,0.3)` | `0 4px 16px rgba(16,185,129,0.3)` |
| `--font-heading` | `'Unbounded'` | `'Cormorant Garamond', serif` |
| `--font-body` | `'Inter'` | `'Manrope', sans-serif` |
| `--font-mono` | `'Fira Code'` | `'JetBrains Mono', monospace` |
| Google Fonts `@import` | Unbounded + Inter + Fira Code | Cormorant Garamond + Manrope + JetBrains Mono |

Also in theme.css Light mode block — same accent replacements.

#### Hardcoded in JSX
| File | Change |
|------|--------|
| ArtistDashboard.jsx | 1 purple rgba → emerald |
| EmployerDashboard.jsx | 3 lines purple → emerald |
| GamificationScreen.jsx | 2 lines purple/blue → emerald |

## Proposed Implementation Strategy

### Approach: PowerShell Bidirectional Script

Create `Scripts/switch_theme.ps1` — a single PowerShell script that:
1. Detects current theme by reading `--cta` from `templates/base.html`
2. If `--cta: #2563EB` → switch to Emerald (A → B)
3. If `--cta: #10B981` → switch to Digital Velvet (B → A)
4. Performs all color + font replacements across all files
5. Updates CSS cache-busting versions
6. Outputs a summary of changed files

### Proposed Changes

- [ ] **1. Create `Scripts/switch_theme.ps1`** — The main bidirectional switch script
  - Detect current theme
  - Define two replacement maps (A→B and B→A)
  - Run through all known files with `(Get-Content).Replace()` chains
  - Handle Google Fonts CDN swap
  - Handle font variable swap
  - Update `?v=X.X.X` cache busters
  - Print summary

- [ ] **2. Create `Scripts/theme_definitions.md`** — Human-readable reference card
  - Side-by-side comparison of both themes
  - Color swatches (hex values)
  - Font stacks
  - Usage examples
  - Instructions for running the switch

- [ ] **3. Test: Run A→B switch**, verify build
- [ ] **4. Test: Run B→A switch**, verify it restores original

### File List for Script to Process

```
# Web (Django)
templates/base.html
static/css/adaptive.css
static/css/animations.css
static/css/mobile.css
static/js/mobile_swipe.js
static/js/notifications.js
core/templates/core/index.html
core/templates/core/catalog.html
core/templates/core/support.html
templates/core/admin/dashboard.html
templates/core/admin/model_edit.html
templates/core/admin/model_list.html
templates/core/conversation.html
templates/core/includes/artists_table.html
templates/core/includes/inbox_list.html
templates/core/includes/jobs_table.html
templates/emails/application_rejected.html
templates/emails/contract_signed.html
templates/emails/email_base.html
templates/emails/kyc_rejected.html
templates/emails/password_reset.html
templates/emails/verification.html
templates/emails/visa_uploaded.html
templates/emails/welcome.html
templates/jobs/applications.html
templates/jobs/contract_view.html
templates/jobs/create_job.html
templates/jobs/dashboard.html
templates/jobs/job_detail.html
templates/jobs/job_detail_content.html
templates/jobs/my_applications.html
templates/jobs/my_jobs.html
templates/jobs/urgent_checkout.html
templates/users/artist_dashboard.html
templates/users/artist_public_content.html
templates/users/employer_public_content.html
templates/users/employer_public_content_V2.html
templates/users/employer_public_content_V3.html
templates/users/employer_public_content_V4.html
templates/users/employer_public_content_backup.html
templates/users/employer_public_content_v4_tabs.html
templates/users/employer_public_content_v5.html
templates/users/includes/fomo_widget_content.html
templates/users/kyc_submit.html
templates/users/login.html
templates/users/password_reset.html
templates/users/password_reset_confirm.html
templates/users/profile.html
templates/users/register.html
templates/users/reviews_list_partial.html
templates/users/subscription.html
templates/users/verification_email.html

# Mobile (Capacitor/Vite)
artconnect-mobile/app/src/styles/theme.css
artconnect-mobile/app/src/screens/ArtistDashboard.jsx
artconnect-mobile/app/src/screens/EmployerDashboard.jsx
artconnect-mobile/app/src/screens/GamificationScreen.jsx
```

### Color Replacement Map (used by script)

```
# ---- CTA / Primary ----
#2563EB  <-->  #10B981
#1D4ED8  <-->  #059669
#2563eb  <-->  #10b981
#1d4ed8  <-->  #059669

# ---- Purple → Emerald ----
#7C3AED  <-->  #10B981
#7c3aed  <-->  #10b981
#7c4dff  <-->  #10B981
#6200ea  <-->  #059669
#a78bfa  <-->  #34D399
#a855f7  <-->  #34D399
#c4b5fd  <-->  #34D399
#6d28d9  <-->  #059669
#8b5cf6  <-->  #10B981
#6f42c1  <-->  #10B981

# ---- RGBA glow replacements ----
rgba(37,99,235,   <-->  rgba(16,185,129,
rgba(37, 99, 235, <-->  rgba(16, 185, 129,
rgba(124,77,255,  <-->  rgba(16,185,129,
rgba(124, 77, 255,<-->  rgba(16, 185, 129,
rgba(139,92,246,  <-->  rgba(16,185,129,
rgba(139, 92, 246,<-->  rgba(16, 185, 129,
rgba(124,58,237,  <-->  rgba(16,185,129,
rgba(124, 58, 237,<-->  rgba(16, 185, 129,
rgba(168,85,247,  <-->  rgba(52,211,153,
rgba(168, 85, 247,<-->  rgba(52, 211, 153,
rgba(111,66,193,  <-->  rgba(16,185,129,
rgba(111, 66, 193,<-->  rgba(16, 185, 129,

# ---- Fonts ----
'Unbounded'          <-->  'Cormorant Garamond'
'Inter'              <-->  'Manrope'
'Fira Code'          <-->  'JetBrains Mono'
# Google Fonts CDN URL swap (special handling)
```

## Verification & Tests
- [ ] Run `switch_theme.ps1` → verify all replacements applied (A→B)
- [ ] Run `npx vite build` in `artconnect-mobile/app/` → no errors
- [ ] Run `switch_theme.ps1` again → verify it restores to A
- [ ] Run `npx vite build` again → no errors
- [ ] Visual check: both themes render correctly

## Estimated Changes
- **Size**: Medium
- **New files**: 2 (switch_theme.ps1, theme_definitions.md)
- **Risk**: Low — script is reversible and non-destructive
