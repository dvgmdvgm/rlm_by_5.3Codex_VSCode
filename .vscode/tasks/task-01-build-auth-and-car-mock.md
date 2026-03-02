# Task 01 — Build Theme Toggle and Theme Tokens

Role: Worker
Status: COMPLETED

## Objective
Implement in `examples/login_page.html`:
- light/dark theme token system
- visible toggle button for switching themes
- full color adaptation across cards, text, inputs, borders, backgrounds, status box, and decorative butterfly
- theme persistence in browser storage

## Constraints
- Frontend only, no backend endpoints.
- Keep red button rule for all clickable action buttons.
- Preserve existing page UX (login, registration, purchase mock, butterfly).

## Output Target
- `examples/login_page.html`

## Worker Result
- Added a visible theme toggle button to switch between light and dark modes.
- Introduced complete tokenized color system for both themes (backgrounds, text, borders, inputs, focus states, cards, status box, decorative butterfly).
- Preserved existing login, registration, and purchase simulation behavior.
- Kept all action buttons red in both themes per canonical UI rule.
- Added localStorage persistence for the selected theme with system-preference fallback.
