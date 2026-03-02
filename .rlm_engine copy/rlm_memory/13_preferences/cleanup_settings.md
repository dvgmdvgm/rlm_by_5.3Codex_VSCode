# 🧹 Cleanup Settings

> **Version**: 1.0.0  
> **Last Updated**: 2026-02-25
> **Modified**: 2026-02-27 (Translated to EN)

---

## ⏳ TTL (Time-to-Live) Settings

Defines how long entries remain active before being flagged for review:

```yaml
TTL_BY_CATEGORY:
  # Context (Volatile)
  07_context/current_session.md: 1      # days
  07_context/pending_tasks.md: 7         # days
  07_context/session_history/*: 30       # days
  07_context/walkthroughs/*: 90          # days
  
  # Problems (Medium-term)
  06_problems/bugs/*: 60                 # days
  06_problems/workarounds/*: 90          # days — should transition to fixes!
  
  # Decisions (Long-term)
  03_decisions/*: 365                    # days
  
  # Architecture (Permanent)
  02_architecture/*: 0                   # 0 = No expiry
  01_project/*: 0                        # 0 = No expiry
  
  # External (Medium-term, APIs change)
  09_external/*: 180                     # days
  
  # Default
  DEFAULT: 180                           # days
```

---

## ⭐ Importance Scoring Settings

```yaml
# Base weights by category (0.0 - 1.0)
BASE_WEIGHTS:
  03_decisions: 0.9      # ADRs are critical
  02_architecture: 0.85  # Architecture is vital
  01_project: 0.8        # Project info is important
  04_domain: 0.75        # Business rules
  05_code: 0.6           # Code documentation
  06_problems: 0.7       # Problems/solutions
  09_external: 0.6       # External dependencies
  07_context: 0.3        # Session context (volatile)
  08_people: 0.5         # People/team info
  10_testing: 0.5        # Testing context
  11_deployment: 0.7     # Deployment info is important
  12_roadmap: 0.4        # Plans evolve
  13_preferences: 0.6    # User settings

# Minimum threshold for categories (protection)
MIN_SCORES:
  03_decisions: 0.5      # Never delete decisions lightly
  02_architecture: 0.4   # Protect architecture docs
  DEFAULT: 0.1

# Score thresholds for automated actions
THRESHOLDS:
  CRITICAL: 0.7          # Never delete automatically
  IMPORTANT: 0.4         # Summarize before deletion
  ARCHIVE: 0.2           # Candidate for archiving
  DELETE: 0.1            # Candidate for deletion
```

---

## 🔄 Automatic Cleanup Settings

```yaml
# When to trigger cleanup checks
CLEANUP_TRIGGERS:
  ON_WAKEUP: true        # Fast check during session start
  ON_SLEEP: true         # Full check during session end
  MANUAL_ONLY: false     # If true, only works via /anchor_cleanup

# Actions to perform on specific items
CLEANUP_ACTIONS:
  # Session history older than TTL
  SESSION_HISTORY:
    action: summarize_and_archive
    keep_summary: true
    
  # Duplicates
  DUPLICATES:
    action: merge
    keep_newest: true
    
  # Empty files
  EMPTY_FILES:
    action: delete
    confirm: false
    
  # Low-score entries
  LOW_SCORE:
    action: prompt_user
    threshold: 0.2
```

---

## 📝 Summarization Settings

```yaml
# How to summarize old records
SUMMARIZATION:
  # Merging session history
  SESSION_MERGE:
    enabled: true
    period: monthly           # daily, weekly, monthly
    max_summary_lines: 50
    keep_decisions: true      # Always preserve decisions
    keep_problems: true       # Always preserve problems
    
  # Topic compression
  TOPIC_COMPRESS:
    enabled: true
    min_files_to_trigger: 5   # Compress when 5+ files share a topic
    
  # Archive summary format
  ARCHIVE_SUMMARY:
    enabled: true
    format: "metadata + 1 paragraph"
```

---

## 📦 Backup Settings

```yaml
BACKUP:
  # Backup storage location
  BACKUP_DIR: ".agent/backups"
  
  # Archive format
  FORMAT: "zip"
  
  # File name pattern
  FILENAME_PATTERN: "anchor_backup_{date}_{time}.zip"
  
  # Auto-backup before risky operations
  AUTO_BACKUP_BEFORE:
    - anchor_remove
    - anchor_cleanup (delete action)
    
  # Retention policy
  MAX_BACKUPS: 5
  
  # Auto-rotation
  AUTO_DELETE_OLD: true
```

---

## 🔐 Safe Removal Settings

```yaml
SAFE_REMOVE:
  # Require confirmation code
  REQUIRE_CODE: true
  
  # Code configuration
  CODE_LENGTH: 8
  CODE_CHARS: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
  
  # Safety backup
  CREATE_BACKUP: true
  
  # Final backup naming
  FINAL_BACKUP_NAME: "anchor_backup_FINAL_{date}.zip"
```

---

## 🔧 Advanced Settings

```yaml
# Performance
MAX_FILES_TO_SCAN: 1000
SCAN_TIMEOUT_SECONDS: 30

# Logging
LOG_CLEANUP_ACTIONS: true
LOG_FILE: ".agent/logs/cleanup.log"

# Dry run mode (Preview what would happen)
DRY_RUN_BY_DEFAULT: true
```
