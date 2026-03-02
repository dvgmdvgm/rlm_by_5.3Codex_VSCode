# ⚙️ Coding Rules — Scenica

> **Imported from**: `GEMINI.md`, `PROJECT_CONTEXT.md`, `design_proposal.md`
> **Date**: 2026-02-06
> **Modified**: 2026-02-27 (Translated to EN)

---

## 🎨 OLED Dark Theme (CRITICAL)

The project uses a **strict OLED Dark (Deep Black) theme**.

### Prohibited ❌

1. Using `bg-white` or `bg-light` without `bg-opacity-10` or lower.
2. Pure white backgrounds — this is an error!
3. White standard scrollbars.
4. **`bg-white bg-opacity-5`** — even with low opacity, this can create a **white/light background** on some devices! Instead, use:
   ```css
   background: rgba(255, 255, 255, 0.03);
   /* or */
   background: rgba(255, 255, 255, 0.05);
   ```

### Forms and Inputs

- All fields (`input`, `select`, `textarea`) must be dark or transparent.
- `<option>` tags must have `background-color: #141416`.
- `autofill` styles must be overridden (no white/yellow backgrounds).
- Placeholders: Light color with reduced opacity.

### Scrollbars

- Track: Transparent.
- Thumb: Dark/Semi-transparent.
- No white standard scrollbars!

### Containers

- Verify transparency nesting.
- Child elements must not overlap parents with an opaque background.

---

## 🎯 Color Palette

| Role | Hex | Description |
|------|-----|-------------|
| **Primary** | `#18181B` | Primary card background |
| **Background** | `#0D0D0F` | Deep black background |
| **CTA** | `#2563EB` | Blue for action buttons |
| **Accent** | `#F59E0B` | Amber/Gold for accents |
| **Secondary** | `#3F3F46` | Secondary elements |

---

## 📐 Typography

- **H1/H2 Headers**: Unbounded (Accent, wide, cinematic handles Cyrillic well).
- **Interface/Body**: Inter (SaaS standard, perfect readability in dark mode).
- **Monospace**: Fira Code (Contract IDs, dates, code snippets).
- **Style**: Minimalist, Digital Velvet.

### Typography Rules (Dark Mode)
1. White `#FFFFFF` is only for H1 (Unbounded). Body text: `#E4E4E7`, Secondary: `#A1A1AA`.
2. UPPERCASE elements (badges, tags): Inter + `letter-spacing: 0.05em`.
3. Minimum font weight — Regular (400), preferred Medium (500). Never use Light/Thin.

```css
@import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap');
```

---

## ✨ UI Patterns

### Glass Cards
- Semi-transparent backgrounds with blur (`backdrop-filter`).
- Glassmorphism style.

### Effects
- Hover transitions: **200-300ms**.
- Large sections: 48px+ gaps.
- Scroll-snap for galleries.
- Large typography: 32px+.

### Mandatory Elements
- [x] `cursor: pointer` on all clickable elements.
- [x] Smooth 200-300ms transitions for hovers.
- [x] No emojis as icons (use Bootstrap Icons / SVG only).
- [x] Responsive targets: 375px, 768px, 1024px, 1440px.

---

## 🔧 Django Templates

### CRITICAL: Syntax Rules

1. **Keep tags on a single line**:
   ```django
   {# ❌ INCORRECT #}
   {% if user == job.employer and not
   app.employer_signature %}
   
   {# ✅ CORRECT #}
   {% if user == job.employer and not app.employer_signature %}
   ```

2. **Spaces around `==`**:
   ```django
   {# ❌ INCORRECT #}
   {% if request.GET.gender=='M' %}
   
   {# ✅ CORRECT #}
   {% if request.GET.gender == 'M' %}
   ```

### Post-HTML Changes

**MANDATORY** execution of the fix script:
```bash
# First, dry-run
python Scripts/fix_django_templates.py --dry-run

# Then, live
python Scripts/fix_django_templates.py
```

---

## 📋 Pre-commit Checklist

- [ ] No white backgrounds.
- [ ] `cursor-pointer` on all clickable elements.
- [ ] Smooth hover transitions.
- [ ] Text contrast ratios of 4.5:1+.
- [ ] Visible focus states.
- [ ] `prefers-reduced-motion` respected.
- [ ] Responsive layouts verified.

---

## 📂 Key Style Files

| File | Purpose |
|------|---------|
| `templates/base.html` | Core styles and variables (inline) |
| `static/css/mobile.css` | **Mobile Adaptation** (~790 lines) |

### mobile.css includes:
- Mobile sidebar and overlay.
- Floating Action Button (FAB) for notifications.
- Touch-friendly elements (`--touch-target-min: 44px`).
- Adaptive forms (prevents iOS zoom).
- Mobile modals.
- Mobile hero sections.
- Skeleton loading states.

---

## 🔄 Cache Busting (CSS Versioning)

### Rule
When modifying HTML files, **update the version in CSS links**:

```html
<link rel="stylesheet" href="{% static 'css/style.css' %}?v=1.0.1">
```

### Version Format
```
?v=MAJOR.MINOR.PATCH
```
- **MAJOR**: Large design changes.
- **MINOR**: New components.
- **PATCH**: Minor fixes (increment on every HTML change).

---

## 🌍 Localization (i18n)

### CRITICAL: All template strings must be translated

Since the site supports multiple languages, **HARDCODED STRINGS** in Russian or English inside HTML are **PROHIBITED**.

**Rule:**
All user-facing strings must be wrapped in `{% trans %}` or `{% blocktrans %}` tags.

```django
{# ❌ INCORRECT #}
<button>Save</button>
<h1>Welcome, {{ user.name }}</h1>

{# ✅ CORRECT #}
<button>{% trans "Save" %}</button>
<h1>{% trans "Welcome," %} {{ user.name }}</h1>
```

**Tag Attributes (placeholder, title, alt):**
```django
{# ❌ INCORRECT #}
<input placeholder="Enter name">

{# ✅ CORRECT #}
<input placeholder="{% trans 'Enter name' %}">
```

---

## 📹 Video and IFrames

### CRITICAL: Embedding Attributes
When embedding video via `<iframe>` (YouTube, etc.), the following attributes are **MANDATORY**:

1. `referrerpolicy="strict-origin-when-cross-origin"`
2. `allowfullscreen`

```html
<iframe src="..." referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
```

---

## 🖥️ PowerShell (Windows) — Command Execution Rules

> **OS: Windows**. All commands must be executed in **PowerShell**.
> Mixing Bash, CMD, and PowerShell syntax is prohibited.

| Error | Why it fails | Replacement ✅ |
|-------|--------------|----------------|
| `mkdir -p path/to` | `-p` is a Bash flag | `New-Item -ItemType Directory -Path 'path\to' -Force` |
| `grep pattern file` | Unix utility | `Select-String -Pattern 'pattern' -Path file` |
| `dir /s /b` | CMD syntax | `Get-ChildItem -Recurse` |
| `rm -rf path` | Bash syntax | `Remove-Item -Recurse -Force 'path'` |
| `cat file` | Alias (use explicit) | `Get-Content file` |

### Escaping `$_` in `-Command "..."` ❌
```powershell
# ❌ INCORRECT — $_ is interpreted as an empty string
powershell -Command "Get-ChildItem | Where-Object { $_.Name -match 'test' }"

# ✅ CORRECT — use single quotes to prevent interpretation
powershell -Command 'Get-ChildItem | Where-Object { $_.Name -match "test" }'
```

### Path Slashes ❌
```powershell
# ❌ INCORRECT — terminal slash escapes the closing quote
Move-Item -Destination "path\to\folder\"

# ✅ CORRECT — no trailing slash
Move-Item -Destination "path\to\folder"
```

### Recommendations
1. **Atomic Commands**: Prefer small, single commands over long pipes.
2. **Explicit PowerShell**: Always use full cmdlet names (`Get-ChildItem`, `New-Item`) instead of aliases.
3. **SafeToAutoRun (Critical)**:
   - For non-destructive operations (read, status, diagnostic, static build), set `SafeToAutoRun: true`.
   - Destructive operations (delete, git reset) require `SafeToAutoRun: false`.

---

---

# --- GENERIC LANGUAGE STANDARDS (added by anchor_update v2.5.1) ---

## 📐 General Philosophy

1. **Explicit > Implicit** — Clear code over clever code
2. **DRY** — Don't Repeat Yourself
3. **KISS** — Keep It Simple, Stupid
4. **YAGNI** — You Aren't Gonna Need It
5. **Single Responsibility** — One function = one purpose
6. **Defensive Programming** — Validate inputs, handle edge cases
7. **Descriptive Naming** — Full words, no abbreviations (`user_name` not `un`)
8. **Comments explain WHY, not WHAT** — Code should be self-documenting

### Naming Anti-patterns (All Languages)

| ❌ Never | ✅ Always |
|----------|-----------|
| `d` | `user_data` |
| `fn` | `calculate_total` |
| `cb` | `on_click_handler` |
| `idx` | `user_index` |
| `tmp` | `cached_response` |
| `e` | `error` / `exception` |
| `res` | `response` |
| `req` | `request` |

### Comments (All Languages)

```
# Single line: Brief explanation

# Multi-line:
# Longer explanation that spans
# multiple lines for clarity

# TODO: Description of what needs to be done
# FIXME: Description of what's broken
# NOTE: Important information
# HACK: Temporary workaround
```

### File Structure Order (All Languages)

```
1. Imports / dependencies
2. Constants / configuration
3. Types / interfaces / models
4. Helper functions (private)
5. Main logic (public API)
6. Entry point / exports
```

### Test Structure (All Languages)

```
Arrange → Act → Assert
```

---


## 🐍 Python

### Formatting

```
INDENTATION=4 spaces
LINE_LENGTH=100
QUOTES=double (")
PYTHON_VERSION=3.10+
LINTER=ruff
TYPE_CHECKER=mypy
```

### Naming Conventions

| Element | Style | Example |
|---------|-------|---------|
| Variables | snake_case | `user_name`, `total_count` |
| Functions | snake_case | `get_user()`, `calculate_total()` |
| Classes | PascalCase | `UserProfile`, `OrderManager` |
| Constants | UPPER_SNAKE | `MAX_RETRIES`, `API_URL` |
| Private | _prefix | `_internal_method()` |
| Type aliases | PascalCase | `UserDict`, `Callback` |

### Type Hints — ALWAYS

```python
from typing import Optional

def find_user(
    user_id: int,
    include_deleted: bool = False,
) -> Optional[User]:
    """Find user by ID with optional include of soft-deleted users."""
    ...
```

### Docstrings (Google Style)

```python
def process_payment(
    amount: Decimal,
    currency: str,
    customer_id: int,
) -> PaymentResult:
    """Process a payment for the given customer.

    Args:
        amount: Payment amount as Decimal. Must be positive.
        currency: ISO 4217 currency code (e.g., "USD", "EUR").
        customer_id: ID of the customer making the payment.

    Returns:
        PaymentResult with transaction ID and status.

    Raises:
        InsufficientFundsError: If customer balance is too low.
        InvalidCurrencyError: If currency code is not supported.
    """
```

### Imports Order

```python
# 1. Standard library
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 2. Third-party
import requests
from sqlalchemy import Column, Integer, String
from flask import Flask, request, jsonify

# 3. Local
from app.models import User, Payment
from app.utils.validators import validate_email
from app.config import settings
```

### Preferred Patterns

```python
# ✅ f-strings
message = f"Hello, {user.name}! You have {count} notifications."

# ✅ Comprehensions (when simple)
active_emails = [u.email for u in users if u.is_active]

# ✅ Context managers
with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

# ✅ dataclasses (Python 3.10+)
from dataclasses import dataclass

@dataclass
class UserProfile:
    name: str
    email: str
    age: int
    is_verified: bool = False

# ✅ match/case (Python 3.10+)
match status_code:
    case 200:
        return parse_response(data)
    case 404:
        raise NotFoundError(url)
    case _:
        raise UnexpectedStatusError(status_code)

# ✅ Enum instead of magic strings
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# ✅ Walrus operator when appropriate
if (match := pattern.search(text)) is not None:
    process(match.group(1))
```

### Error Handling

```python
# ✅ Specific exceptions, not bare except
try:
    user = await db.get_user(user_id)
except UserNotFoundError:
    logger.warning(f"User {user_id} not found")
    return ErrorResponse(404, "User not found")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    return ErrorResponse(500, "Internal server error")
```

---


## 🌐 JavaScript / TypeScript

### Formatting

```
INDENTATION=2 spaces
QUOTES=single (')
SEMICOLONS=yes
MODULE_SYSTEM=ES modules (import/export)
```

### Naming Conventions

| Element | Style | Example |
|---------|-------|---------|
| Variables | camelCase | `userName`, `totalCount` |
| Functions | camelCase | `getUser()`, `calculateTotal()` |
| Classes | PascalCase | `UserProfile`, `OrderManager` |
| Interfaces | PascalCase | `UserProfile`, `CreateOrderRequest` |
| Type aliases | PascalCase | `OrderStatus`, `ApiResult` |
| Constants | UPPER_SNAKE | `MAX_RETRIES`, `API_URL` |
| Components (React) | PascalCase | `UserCard`, `NavBar` |
| Files | kebab-case | `user-profile.ts`, `order-status.ts` |
| Booleans | semantic prefix | `isActive`, `hasPermission`, `canEdit` |
| Generics | T prefix | `TValue`, `TResult`, `TEntity` |

### TypeScript — Type-First Design

```typescript
// ✅ Interfaces for object shapes
interface CreateUserRequest {
  readonly name: string;
  readonly email: string;
  readonly role: UserRole;
  readonly metadata?: Record<string, unknown>;
}

// ✅ Discriminated unions
type ApiResult<T> =
  | { success: true; data: T }
  | { success: false; error: string; code: number };

// ✅ Branded types for primitives
type UserId = string & { readonly __brand: 'UserId' };
type Email = string & { readonly __brand: 'Email' };

// ✅ satisfies instead of as
const config = {
  port: 3000,
  host: 'localhost',
} satisfies ServerConfig;

// ✅ Type guards
function isUser(value: unknown): value is User {
  return typeof value === 'object' && value !== null && 'id' in value;
}

// ✅ Exhaustive switch
function getStatusLabel(status: OrderStatus): string {
  switch (status) {
    case 'pending': return 'Pending';
    case 'completed': return 'Completed';
    default: {
      const _exhaustive: never = status;
      throw new Error(`Unknown status: ${_exhaustive}`);
    }
  }
}
```

### Async/Await

```typescript
// ✅ async/await over .then() chains
async function fetchUserProfile(userId: string): Promise<UserProfile> {
  const response = await fetch(`/api/users/${userId}`);
  if (!response.ok) {
    throw new ApiError(`Failed to fetch user: ${response.status}`);
  }
  return response.json();
}

// ✅ Parallel requests
const [user, orders, notifications] = await Promise.all([
  fetchUser(userId),
  fetchOrders(userId),
  fetchNotifications(userId),
]);
```

### Functions

```javascript
// ✅ Arrow functions for callbacks
const items = data.map((item) => item.name);

// ✅ Named functions for exports
export function getUserById(id) {
  // ...
}
```

---


## ⚛️ React (JSX/TSX)

### Component Style

```tsx
// ✅ Functional components + hooks, NEVER class components
interface UserCardProps {
  readonly user: User;
  readonly onEdit?: (userId: string) => void;
  readonly variant?: 'compact' | 'full';
}

export function UserCard({ user, onEdit, variant = 'full' }: UserCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleEdit = useCallback(() => {
    onEdit?.(user.id);
  }, [onEdit, user.id]);

  return (
    <div className="user-card">
      <h3>{user.name}</h3>
      {onEdit && (
        <button onClick={handleEdit} type="button">Edit</button>
      )}
    </div>
  );
}

// ✅ Custom hooks with use prefix
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

---


## 🗄️ SQL

### Formatting

```
KEYWORDS=UPPERCASE (SELECT, FROM, WHERE, JOIN)
IDENTIFIERS=snake_case
TABLES=singular (user, order, payment)
INDENT=2 or 4 spaces for sub-clauses
```

### Idioms

```sql
-- ✅ CTE instead of nested subqueries
WITH active_users AS (
    SELECT id, name, email, created_at
    FROM "user"
    WHERE is_active = TRUE
      AND last_login_at > CURRENT_DATE - INTERVAL '30 days'
),
user_orders AS (
    SELECT user_id, COUNT(*) AS order_count,
           SUM(total_amount) AS total_spent
    FROM "order"
    WHERE status = 'completed'
    GROUP BY user_id
)
SELECT
    au.name,
    au.email,
    COALESCE(uo.order_count, 0) AS order_count,
    COALESCE(uo.total_spent, 0.00) AS total_spent
FROM active_users au
LEFT JOIN user_orders uo ON uo.user_id = au.id
ORDER BY uo.total_spent DESC NULLS LAST
LIMIT 100;

-- ✅ Safe migrations
ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ DEFAULT NULL;

-- ✅ Concurrent indexes for production
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    idx_user_email ON "user" (email);
```

---

