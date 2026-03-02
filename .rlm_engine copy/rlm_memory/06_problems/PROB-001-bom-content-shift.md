# BOM (Byte Order Mark) causing 24px content shift

**Date Discovered:** 2026-02-10  
**Status:** ✅ Resolved  
**Priority:** High  
**Modified**: 2026-02-27 (Translated to EN)

---

## Description

On the `/jobs/my/` page (and others), the `h2` header was shifted **24px downwards** compared to `/dashboard/`. The container started at `124px` instead of the expected `100px`.

---

## Root Cause

Template files (`.html`) were saved in **UTF-8 with BOM** (Byte Order Mark) encoding. BOM (`\ufeff`, 3 bytes: `EF BB BF`) is an invisible character at the beginning of a file.

### How BOM breaks the layout:

1. A BOM in `my_jobs.html` placed before `{% extends "base.html" %}` ends up at the start of the rendered HTML — **before** the `<!DOCTYPE html>`.
2. The browser encounters a character before the DOCTYPE and switches to **quirks mode** or misinterprets the `<head>`.
3. Tags like `<meta>`, `<title>`, and `<link>` are pushed into the `<body>` instead of staying in the `<head>`.
4. The BOM is rendered as an **anonymous text node** with a height of `24px` (1 line of text = `line-height 1.5 × 16px`).
5. This node pushes the `div.container` down by 24px.

### Why Dashboard was unaffected:
`dashboard.html` **did not have a BOM** — different editors or saving operations had been applied to different files.

---

## Affected Files (17 total)

```
templates/base.html
templates/core/includes/jobs_cards.html
templates/core/includes/pagination.html
templates/core/includes/search_panel.html
templates/jobs/applications.html
templates/jobs/contract_view.html
templates/jobs/create_job.html
templates/jobs/employer_jobs_full.html
templates/jobs/job_detail.html
templates/jobs/job_detail_content.html
templates/jobs/my_applications.html
templates/jobs/my_jobs.html
templates/users/artist_public.html
templates/users/artist_public_content.html
templates/users/employer_public_content.html
templates/users/login.html
templates/users/profile.html
templates/users/register.html
```

---

## Resolution

A script `scripts/remove_bom.py` was created to:
- Scan all `.html` files in the `templates/` directory.
- Identify files containing a BOM.
- Remove the BOM (the first 3 bytes `EF BB BF`).

```bash
python scripts/remove_bom.py
```

> **IMPORTANT:** Run this script after any HTML template modifications, as some editors (Notepad, VS Code with specific settings) may automatically re-insert the BOM upon saving.

---

## Debugging Process

1. Added a JS debug script to `page_header.html` — it measured `h2 top`, `nav height`, and `gap`.
2. Results: Dashboard gap = 48px, My Jobs gap = 69px (a difference of 21px on mobile / 24px on desktop).
3. Browser DOM inspection revealed an anonymous text node with BOM `\ufeff` before the content.
4. `XMLHttpRequest` confirmed: My Jobs HTML started with `charCode 0xFEFF`, while Dashboard started with `0x3C` (`<`).
5. The Python script detected BOMs in 17 files.

---

## Prevention

- Configure your editor to save in **UTF-8 without BOM**.
- VS Code: Set `"files.encoding": "utf8"` (this is the default and omits the BOM).
- Consider adding `scripts/remove_bom.py` to a pre-commit hook or CI pipeline.
