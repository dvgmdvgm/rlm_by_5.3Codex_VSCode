# 🐛 Chart.js resetting header font-size

> **Date**: 2026-02-10
> **Status**: ✅ Fixed
> **Severity**: High (Visual bug on the main dashboard)
> **Modified**: 2026-02-27 (Translated to EN)

---

## Description

On the Dashboard page (`/dashboard/`), the `h2` header was rendered **half as large** as on other pages (e.g., `/jobs/my/`).

- Dashboard: `font-size: 14px` ❌
- My Jobs: `font-size: 28px` ✅

Both pages use the **exact same component** `page_header.html` with identical HTML markup.

---

## Root Cause

**Chart.js 4.4.1** (loaded in `dashboard.html`, line 312) injects a global CSS reset upon initialization, which overrides the `font-size` of page elements. As a result, the `h2` loses its Bootstrap styling (`2rem`) and inherits a default `14px` from its parent.

```html
<!-- dashboard.html, line 312 -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
```

---

## Resolution

An **inline style** `font-size: 2rem` was added directly to the `h2` tag within `page_header.html`:

```html
<h2 class="text-white fw-800 mb-1" style="font-size: 2rem;">
```

Inline styles have the highest precedence in the CSS cascade and cannot be overridden by external libraries.

---

## Debugging Process

### Step 1: Verification of HTML Render
Compared the rendered HTML of both pages via the Django shell — the `<h2>` tags and their classes were identical.

### Step 2: JS Debug Panel (Crucial Method)
Added a temporary JavaScript snippet to `page_header.html` to display **computed styles** directly on the page:

```html
<!-- TEMPORARY DEBUG - insert into page_header.html to debug CSS -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    var h2 = document.querySelector('h2.fw-800');
    if (h2) {
        var cs = window.getComputedStyle(h2);
        var parentInfo = [];
        var el = h2;
        for (var i = 0; i < 5 && el; i++) {
            var pcs = window.getComputedStyle(el);
            parentInfo.push(el.tagName + '.' + el.className.split(' ').slice(0,2).join('.') + ':' + pcs.fontSize);
            el = el.parentElement;
        }
        var info = 'h2 Font: ' + cs.fontSize + ' | Chain: ' + parentInfo.join(' > ');
        var dbg = document.createElement('div');
        dbg.style.cssText = 'position:fixed;bottom:10px;left:10px;background:red;color:white;padding:8px 16px;border-radius:8px;z-index:99999;font-size:12px;font-family:monospace;max-width:90vw;word-break:break-all;';
        dbg.textContent = info;
        document.body.appendChild(dbg);
    }
});
</script>
```

This script allowed us to see:
- The **actual computed font-size** of the element.
- The **inheritance chain** of the font-size from the element up to the 5th parent.

The results confirmed that on the Dashboard, the `h2` was receiving `14px` (inherited from body), whereas on My Jobs, it correctly received `28px` (Bootstrap's `h2` style).

### Step 3: Identifying the Culprit
Determined that the only difference between the Dashboard and other pages was the loading of **Chart.js 4.4.1** via CDN.

---

## Key Learning

> **External JS libraries (like Chart.js) can inject global CSS resetting styles** that override Bootstrap and custom CSS. Always use **inline styles or !important** for critical UI elements on pages that load external third-party libraries.
