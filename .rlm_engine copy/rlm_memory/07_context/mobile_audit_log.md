# 🔍 Mobile UX Audit Log (Internal Memory)

## 🏁 Guest Flow (Audited: 2026-02-22)
| Issue ID | Page | Component | Description | Severity | Status |
|----------|------|-----------|-------------|----------|--------|
| AUDIT-01 | Home | Hero Section | Buttons centered but too close; text wraps poorly. | 🟡 Medium | Pending |
| AUDIT-02 | Catalog | Artist Search | Header says "Поиск Артов" instead of "Поиск Артистов". | 🟠 High | ✅ Fixed |
| AUDIT-03 | Catalog | Job Details | Salary format "1 / 33 EUR" is confusing/broken. | 🟠 High | ✅ Fixed |
| AUDIT-04 | Catalog | Artist Modal | Missing explicit "Close" button (X). | 🟠 High | Pending |
| AUDIT-05 | Register | Form | Password hints make form too long on mobile. | 🟡 Medium | Pending |

## 🔍 Artist Flow (Audited: 2026-02-22)
| Issue ID | Page | Component | Description | Severity | Status |
|----------|------|-----------|-------------|----------|--------|
| AUDIT-08 | Dashboard| Layout | No vertical stacking for stats widgets. | 🔴 Critical | ✅ Fixed |
| AUDIT-09 | All | Container | Large horizontal scroll (Index marquee). | 🔴 Critical | ✅ Fixed |
| AUDIT-10 | Profile | Edit Form | 2-column layout for inputs does not stack. | 🔴 Critical | ✅ Fixed |
| AUDIT-11 | Catalog | Cards | 2-column grid makes cards too narrow. | 🟠 High | ✅ Fixed (CSS) |
| AUDIT-13 | Navbar | Links | Navigation items not hidden (Sidebar logic). | 🟡 Medium | ✅ Fixed |

## 🔍 Employer Flow (Audited: 2026-02-22)
| Issue ID | Page | Component | Description | Severity | Status |
|----------|------|-----------|-------------|----------|--------|
| AUDIT-14 | General | Settings | `EMAIL_RESEND_INTERVAL` missing, causing crash. | 🔴 Critical | ✅ Fixed |
| AUDIT-15 | Create Job| Form | Date input placeholder has leading comma. | 🟠 High | ✅ Fixed |
| AUDIT-16 | Dashboard| Banner | Resend button too close to screen edge. | 🟡 Medium | Pending |
| AUDIT-17 | General | Modals | Modal badges overlap with text. | 🟡 Medium | Pending |
