# Bug: Mobile modal shifting 5-10px during scroll

**Date:** 2026-02-10  
**Status:** ✅ Fixed  
**File:** `templates/base.html`
**Modified**: 2026-02-27 (Translated to EN)

---

## Issue

On physical mobile devices (Android Chrome), modal windows (Bootstrap 5 `.modal`) were shifting by 5-10 pixels when a scroll was attempted. Shifting downwards would cut off the top part of the modal, while shifting upwards would cut off the bottom.

---

## Root Cause

Bootstrap's `.modal` uses `overflow-y: auto`, which creates a minimal scroll area. On Android Chrome, the address bar changes height during scroll, exacerbating the viewport stability issue.

---

## Final Solution (CSS-only)

**Core Concept:** Using `overflow-y: scroll` (instead of `auto`) on `#modal-content-body` forces it to ALWAYS be a scroll container, even when the content fits. This allows `overscroll-behavior: none` to reliably block chain-scrolling up to the parent `.modal`.

```css
@media (max-width: 991px) {
    /* Block scroll on Bootstrap overlay */
    #universalModal.modal {
        overflow: hidden !important;
        padding: 0 !important;
        touch-action: none;
    }
    /* Block scroll on dialog */
    #universalModal .modal-dialog.custom-modal-size {
        overflow: hidden !important;
        touch-action: none;
    }
    /* Scroll ONLY inside the content area */
    #modal-content-body {
        overflow-y: scroll;          /* IMPORTANT: scroll, not auto! */
        overscroll-behavior: none;   /* Blocks chain-scrolling */
        touch-action: pan-y;         /* Allows only vertical touch gestures */
        max-height: 90dvh !important;
    }
}
```

**JavaScript part:** The `body` is fixed (`position: fixed`) when the modal opens — a standard technique for locking background scrolling.

---

## What DID NOT Work

1. `overflow: hidden !important` on `.modal` — the browser often ignores this for touch events.
2. `touch-action: none` via CSS only — failed to block scrolling on Android Chrome.
3. `overscroll-behavior: none/contain` with `overflow-y: auto` — fails when the element is NOT an active scroll container (if content fits, `auto` doesn't create a scroll zone).
4. `position: fixed; bottom: 0` on `.modal-dialog` — broke positioning (modal jumped to the top).
5. JS `e.preventDefault()` on `touchmove` — worked for short modals but caused lag and "sticking" when scrolling long content (e.g., employer views).

---

## Key Learnings

1. `overflow-y: scroll` vs `auto` — the distinction is critical. `scroll` ALWAYS creates a scroll container, enabling `overscroll-behavior` even for short content.
2. JS touchmove handlers cause noticeable mobile performance lag — prioritize CSS-only approaches.
3. Combining `touch-action: none` on parents with `touch-action: pan-y` on the scroll container is the correct way to isolate touch gestures.
