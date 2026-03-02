# 🔔 Automated Contract Completion Notifications

Toolkit for automatically notifying both parties (employer and artist) when a contract end date is reached, including a prompt to leave a review.

---

## 🛠️ Implementation

The system operates on a two-level principle:

1.  **Active Check (Real-time)**: Triggers whenever a user visits any page on the site.
    -   Called via `jobs/context_processors.py`.
    -   Uses the `check_user_contract_reviews(user)` function from `jobs/utils.py`.
2.  **Background Check (Batch)**: Designed for scheduled execution on the server.
    -   Management Command: `python manage.py check_contracts`.
    -   Located in `jobs/management/commands/check_contracts.py`.

---

## 🗄️ Database Changes

Two flags were added to the `Application` model to prevent duplicate notifications:
-   `employer_review_notified` (bool)
-   `artist_review_notified` (bool)

---

## 🚀 Production Server Configuration

To ensure notifications are sent even to users who haven't logged in for a while, the background command must be scheduled.

### 1. On Linux (Ubuntu/Debian) via CRON
Run `crontab -e` and add the following line (runs daily at midnight):
```bash
0 0 * * * /path/to/your/venv/bin/python /path/to/your/project/manage.py check_contracts >> /path/to/your/logs/contracts.log 2>&1
```

### 2. On Windows via Task Scheduler
1.  Create a `.bat` file:
    ```batch
    C:\path\to\venv\Scripts\python.exe C:\path\to\project\manage.py check_contracts
    ```
2.  Add this file to the Windows Task Scheduler with a daily recurrence.

---

## 📱 Future Expansion (Mobile Push)
When implementing the mobile app, it is sufficient to add a Push service call to the `create_notification` function in `jobs/utils.py`. All contract filtering logic is already in place.
