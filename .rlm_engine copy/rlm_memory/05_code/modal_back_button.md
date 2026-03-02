# Native Back Button for Modal Windows

- **Date**: 2026-02-17
- **Tags**: modal, back-button, popstate, pushState, bootstrap, capacitor, UX
- **Modified**: 2026-02-27 (Added mobile app convention)

---

## Rule

When a modal window is open, the "Back" button (browser back) should **close the modal**, NOT navigate away from the page. Only a subsequent press of "Back" should trigger navigation. This rule applies to **all pages** on the site.

---

## Technical Implementation (in `base.html`, global)

### Mechanism: `pushState` + `popstate`

```javascript
// 1. When a modal is shown -> push a dummy-state to the history
document.addEventListener('shown.bs.modal', function() {
    if (!modalHistoryPushed) {
        history.pushState({ modalOpen: true }, '');
        modalHistoryPushed = true;
    }
});

// 2. When a modal is hidden NOT via the back button -> remove the dummy-state
document.addEventListener('hidden.bs.modal', function() {
    if (modalHistoryPushed && !isBackNavigating) {
        modalHistoryPushed = false;
        history.back(); // pop the dummy state silently
    } else {
        modalHistoryPushed = false;
    }
});

// 3. When the browser "Back" is pressed -> the popstate event closes the modal
window.addEventListener('popstate', function(event) {
    if (modalHistoryPushed) {
        modalHistoryPushed = false;
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            bootstrap.Modal.getInstance(openModal).hide();
        }
        return; // prevent default navigation
    }
    // ... other popstate handlers (sidebar, notifications, etc.)
});
```

### Key Guidelines

1. **DO NOT** duplicate `popstate` handlers on individual pages — everything is centralized in `base.html`.
2. **DO NOT** push state inside specific `openModal()` functions — the global `shown.bs.modal` listener handles this automatically.
3. The `isBackNavigating` flag prevents race conditions during modal closing.
4. This mechanism works for **all** Bootstrap modals (universal modal, streak, FOMO, gamification, etc.).

### Location in Codebase

- **File**: `templates/base.html`
- **Section**: `// ===== NATIVE BACK-BUTTON FOR MODALS =====`
- **Precedence**: In the `popstate` listener, modals are handled FIRST (before sidebar, notifications, etc.).

---

## Mobile App (React / Capacitor)

### Architecture: `ModalOverlay` + `useBackClose` + `modalRegistry`

The mobile app uses a **three-layer** system:

1. **`modalRegistry.js`** — Global stack of modal close handlers
2. **`useBackClose` hook** — Pushes fake history entry + registers in stack
3. **`ModalOverlay` component** — Universal wrapper that applies both automatically

### Convention (MANDATORY)

**All new modals MUST use `<ModalOverlay>`** — back-close behavior is automatic.

```jsx
// ✅ CORRECT — ModalOverlay handles everything
import ModalOverlay from '../components/ModalOverlay';

{showModal && (
  <ModalOverlay onClose={() => setShowModal(false)}>
    <div className="my-modal" onClick={e => e.stopPropagation()}>
      {/* modal content */}
    </div>
  </ModalOverlay>
)}
```

```jsx
// ❌ WRONG — Do NOT use manual createPortal + useBackClose
import { createPortal } from 'react-dom';
import useBackClose from '../hooks/useBackClose';
useBackClose(showModal, () => setShowModal(false));
{showModal && createPortal(<div className="confirm-overlay">...</div>, document.body)}
```

### How It Works

1. **Modal opens** → `useBackClose` pushes `history.pushState({modal:true}, '')` + registers `onClose` in `modalRegistry` stack
2. **Hardware back / gesture** → Capacitor `backButton` fires → `App.jsx` calls `dismissTopModal()` → pops the top modal from stack → calls its `onClose`
3. **Modal closed by UI** (tap X, overlay click) → `popstate` listener fires → cleanup without double-close
4. **No modals open** → Back button triggers normal `navigate(-1)` or `App.minimizeApp()`

### Files

| File | Purpose |
|------|---------|
| `artconnect-mobile/app/src/components/ModalOverlay.jsx` | Universal wrapper (createPortal + useBackClose) |
| `artconnect-mobile/app/src/hooks/useBackClose.js` | Hook: pushState + popstate + registry |
| `artconnect-mobile/app/src/services/modalRegistry.js` | Global stack: register/dismiss/hasOpen |
| `artconnect-mobile/app/src/App.jsx` | Capacitor backButton → `dismissTopModal()` first |

### Key Guidelines (Mobile)

1. **ALWAYS use `<ModalOverlay>`** — never manual `createPortal` + `useBackClose` in new code.
2. `onClick={e => e.stopPropagation()}` on the inner modal div to prevent overlay-click from closing.
3. Custom class: `<ModalOverlay className="my-class">` (default: `confirm-overlay`).
4. Stack supports **nested modals** — back button closes innermost first.
5. Components already refactored: `ConfirmDialog`, `ActionPicker`, `DocumentUploader`, `SignaturePad`, `ContractViewScreen` doc-preview, `JobApplicationsScreen` inline dialog.
