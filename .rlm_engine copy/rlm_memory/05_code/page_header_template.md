# Standard Page Header Template

## Component: `core/includes/page_header.html`

Usage:
```django
{% include "core/includes/page_header.html" with 
    title="My" 
    title_accent="applications" 
    badge="Artist Dashboard" 
    subtitle="History of your contract requests"
    action_url="/catalog/"
    action_icon="bi-search"
    action_text="Find work"
%}
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | ✅ | Primary header text (before the accent) |
| `title_accent` | ❌ | Accentuated part of the header (text-cta) |
| `badge` | ❌ | Dashboard badge (e.g., "Artist Dashboard") |
| `subtitle` | ❌ | Description text below the header |
| `action_url` | ❌ | URL for the primary action button |
| `action_icon` | ❌ | Bootstrap icon class (e.g., "bi-search") |
| `action_text` | ❌ | Text for the action button |

## Styles

- **Header**: `text-white fw-800 mb-1` (h2)
- **Accent**: `text-cta` (blue with glow effect)
- **Badge**: `rgba(255,255,255,0.06)`, uppercase, letter-spacing: 1px
- **Subtitle**: `text-dim small`
- **Button**: `btn-primary rounded-pill shadow-glow`

## Implementation Status

| Page | File | Status |
|------|------|--------|
| My Applications | `jobs/my_applications.html` | ✅ |
| My Jobs | `jobs/my_jobs.html` | ✅ |
| Profile Settings | `users/profile.html` (Custom design) | ⏳ |
| Candidates | `jobs/applications.html` (Dynamic header) | ⏳ |
| Company Jobs | `jobs/employer_jobs_full.html` (Includes back button) | ⏳ |
