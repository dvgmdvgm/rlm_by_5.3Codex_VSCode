# 📝 Spec: Geography & Navigation Fixes
> Date: 2026-02-28
> Origin: /anchor_plan

## 🎯 Objective
Fix two bugs:
1. **Status bar overlap** — TopBar on GeographyScreen is covered by the OS status bar (no safe-area inset)
2. **Back navigation → blank screen** — TopBar ignores `onBack` prop; hardware back sometimes leaves user on blank page

---

## 🏗️ Architecture & Context

- **Framework**: React + react-router-dom (HashRouter) + Capacitor for Android
- **Main Files Involved**:
  - `artconnect-mobile/app/src/screens/GeographyScreen.jsx` — target screen
  - `artconnect-mobile/app/src/screens/GeographyScreen.css` — screen styles
  - `artconnect-mobile/app/src/components/TopBar.jsx` — shared header component
  - `artconnect-mobile/app/src/styles/theme.css` — global CSS (`.top-bar` definition at line 136)
  - `artconnect-mobile/app/src/App.jsx` — router + hardware back button handler (line 110–137)

---

## 🐛 Root Cause Analysis

### Bug 1 — Status bar overlap
- `.top-bar` CSS: `padding: 14px 16px` (no safe-area inset)  
- Screens with TabBar (AppLayout) don't add safe-area top either — TopBar simply overlaps status bar on all full-screen routes
- `GeographyScreen` renders `<div className="screen">` → the `.screen` class has NO CSS definition → no padding-top for safe area
- **Fix location**: `.top-bar` in `theme.css` — change top padding to include `env(safe-area-inset-top, 0px)`

### Bug 2 — Blank screen on back
Two separate sub-issues:

**2a — No in-app back button**  
`TopBar` props: `{ title, showBack=false, rightAction, leftExtra, onTitleClick }`  
`GeographyScreen` passes `onBack={() => navigate(-1)}` — but `onBack` is NOT a declared prop in TopBar → silently ignored → no back button renders in the UI

**2b — Hardware back leaves blank screen**  
`App.jsx` backButton handler logic:
```js
if (isHome) → minimizeApp()
else if (isMainTab) → navigate('/', replace)
else if (canGoBack) → navigate(-1)
else → minimizeApp()      ← BUG: when canGoBack=false but location is /geography, 
                             app minimizes → user reopens → still on geography → loop
```
`canGoBack` from Capacitor can be `false` even with history entries (HashRouter / Android WebView quirk).  
When `navigate(-1)` runs but the previous hash entry is empty (`#` instead of `#/`), React Router renders no matching route → blank screen.

---

## 🛠️ Proposed Changes

### Fix 1 — Safe area top padding for TopBar

**File**: `artconnect-mobile/app/src/styles/theme.css`  
Change `.top-bar` padding so it always accounts for status bar height:
```css
/* BEFORE */
padding: 14px 16px;

/* AFTER */
padding: calc(14px + env(safe-area-inset-top, 0px)) 16px 14px;
```
- [ ] Apply this change to `.top-bar` in `theme.css` (~line 140)
- [ ] Bump CSS version in any `?v=` cache-bust string if present in `index.html` or template

---

### Fix 2a — TopBar: support `onBack` prop

**File**: `artconnect-mobile/app/src/components/TopBar.jsx`

- [ ] Add `onBack = null` to the props destructuring
- [ ] Show back button when `showBack === true` OR `onBack !== null`
- [ ] When back button clicked: call `onBack()` if provided, otherwise call `navigate(-1)`

```jsx
// Props:
export default function TopBar({ title, showBack = false, onBack = null, rightAction = null, leftExtra = null, onTitleClick = null }) {
  const navigate = useNavigate();
  const handleBack = onBack || (() => navigate(-1));
  const showBackBtn = showBack || onBack !== null;
  ...
  // In JSX:
  {showBackBtn && (
    <button className="top-bar__action" onClick={handleBack}>
      <svg ...back arrow.../>
    </button>
  )}
```

---

### Fix 2b — Hardware back button: never trap user on non-main screen

**File**: `artconnect-mobile/app/src/App.jsx` (~line 110–137)

Current fallback: `else → CapApp.minimizeApp()` — traps user  
Fix: If we're NOT on a main tab and cannot go back in browser history, navigate home instead of minimizing:

```jsx
// BEFORE:
} else if (canGoBack) {
  navigate(-1);
} else {
  CapApp.minimizeApp();
}

// AFTER:
} else if (canGoBack) {
  navigate(-1);
} else {
  // If we're on a sub-page but history is empty (e.g., cold app launch to deep link),
  // go home explicitly instead of minimizing
  navigate('/', { replace: true });
}
```

Also, add safety net for blank hash: in `AppRoutes`, add a `catch-all` route that redirects to home:
```jsx
<Route path="*" element={<Navigate to="/" replace />} />
```
This ensures any unmatched route (including blank `#`) resolves to HomeScreen.

- [ ] Update backButton handler in `App.jsx`
- [ ] Add `<Route path="*" element={<Navigate to="/" replace />}/>` at bottom of route list in `App.jsx`

---

## ✅ Verification & Tests

- [ ] Build Android APK: `cd artconnect-mobile && npm run build` (or `build_android.bat`)
- [ ] Verify: Open GeographyScreen → TopBar is below status bar, not overlapping
- [ ] Verify: Press in-app back on GeographyScreen → returns to previous screen
- [ ] Verify: Press hardware back on GeographyScreen → returns to previous screen (not blank, not minimized)
- [ ] Verify: From cold app start (kill + reopen) → press geography → press back → goes home

---

## 📊 Estimated Impact

| Area | Scope |
|------|-------|
| Files changed | 3 (frontend only) |
| Risk | Low — isolated fixes, no model changes |
| Size | Small |
