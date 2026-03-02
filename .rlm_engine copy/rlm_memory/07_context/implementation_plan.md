# Mobile UX Audit & Refinement Plan

This plan covers a full visual and functional audit of the Scenica mobile interface to ensure it meets premium OLED Dark design standards and provides an excellent user experience.

## Proposed Changes

### 🔍 Discovery & Audit
- **Role Scenarios**: Test as Guest, Artist, and Employer.
- **Components to Check**:
  - Header/Navigation (Menu, Profile links)
  - Home Page (Hero, Sections)
  - Catalog (Search, Filters, Cards)
  - Dashboard (Stats, Lists, Widgets)
  - Forms (Auth, Profile Edit, Job Post)
  - Modals & Toasts
- **Criteria**:
  - OLED Dark consistency (`#0D0D0F` bg, `#18181B` cards)
  - Touch target size (min 44px)
  - Text wrapping and font sizes
  - Spacing (vertical rhythm, padding)
  - Animations (smoothness, duration)

### 🛠️ Execution (Bug Fixes & Tweaks)
- **Critical Fixes**: Immediate resolution of 404s, functional crashes, or blocking UI bugs.
- **Styling Refinements**: Batch CSS updates in `mobile.css` or `base.html` to fix layout issues.

## Verification Plan

### Automated Tests
- No specific automated mobile UI tests exist in the project yet (will check `tests/` directory).
- I will use the **Browser Subagent** to navigate and capture screenshots of all identified pages.

### Manual Verification
1.  **Browser Subagent Validation**:
    - Open `http://127.0.0.1:8000/` in mobile viewport (e.g., iPhone 12/Pro).
    - Navigate through the mapped scenarios.
    - Check console logs for errors.
2.  **User Review**:
    - A detailed `walkthrough_mobile_audit.md` will be provided with findings and fixes.
    - User can verify specific pages on their own device.
