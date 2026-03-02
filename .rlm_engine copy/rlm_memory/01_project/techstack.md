# 🛠 Tech Stack — Scenica

> **Imported from**: `PROJECT_CONTEXT.md`, `requirements.txt`
> **Date**: 2026-02-06
> **Modified**: 2026-02-27 (Translated to EN)

---

## Core Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Backend** | Django | 5.0+ |
| **Frontend** | HTML/CSS + Bootstrap 5 | - |
| **JavaScript** | Vanilla JS | - |
| **Database** | SQLite (dev) / PostgreSQL (prod) | - |
| **Static files** | Whitenoise | 6.6+ |

---

## Django Apps

```
project/
├── config/        # Django config (settings, urls, asgi/wsgi)
├── core/          # Core: views, context_processors, consumers (WebSocket)
├── jobs/          # Jobs, applications, contracts, notifications
├── users/         # Auth, profiles (Artist/Employer), reviews
├── templates/     # HTML templates
└── static/        # CSS, JS, images
```

---

## Key Dependencies

### Forms & UI
- `django-crispy-forms` >= 2.1
- `crispy-bootstrap5` >= 2024.2

### Geodata
- `django-countries` >= 7.5

### WebSocket (Realtime)
- `channels` >= 4.0.0
- `channels-redis` >= 4.2.0
- `daphne` >= 4.0.0

### Files & Media
- `Pillow` >= 10.0.0

### PDF (Contracts)
- `reportlab` >= 4.0.0
- `fpdf2` >= 2.7.0

### REST API
- `djangorestframework` >= 3.14.0

### Payments
- `stripe` >= 7.0.0

---

## Environment Variables

Using `.env` files:
- `.env` — Production secrets
- `.env.example` — Developer template

---

## Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver
```

Or via `start server.bat` (Windows).
