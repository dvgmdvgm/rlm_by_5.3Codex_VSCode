# 📝 Auto-Save Rules

> **Version**: 1.0.0  
> **Last Updated**: 2026-02-05
> **Modified**: 2026-02-27 (Translated to EN)

---

## 💡 Concept

This file defines patterns that trigger automatic memory saving without asking the user.

---

## 🔄 AUTO_SAVE Patterns

These patterns trigger AUTOMATIC saving (no confirmation needed):

### 1. Architectural Decisions (ADR)
```yaml
CATEGORY: 03_decisions
TRIGGERS:
  - "we decided"
  - "chose to use"
  - "will use"
  - "going with"
  - "decided to"
  - "determined that"
  - "selection of"
CONFIDENCE: 0.9
TTL: 365
IMPORTANCE_BASE: 0.9
```

### 2. Bug Fixes & Workarounds
```yaml
CATEGORY: 06_problems
TRIGGERS:
  - "bug"
  - "fixed"
  - "workaround"
  - "hack"
  - "temporary solution"
  - "hotfix"
  - "issue resolved"
CONFIDENCE: 0.8
TTL: 90
IMPORTANCE_BASE: 0.7
```

### 3. External Integrations
```yaml
CATEGORY: 09_external
TRIGGERS:
  - "API key"
  - "endpoint"
  - "integration with"
  - "webhook"
  - "SDK"
  - "third-party"
CONFIDENCE: 0.7
TTL: 180
IMPORTANCE_BASE: 0.6
```

### 4. Architecture Changes
```yaml
CATEGORY: 02_architecture
TRIGGERS:
  - "architecture"
  - "component"
  - "pattern"
  - "data flow"
  - "system design"
  - "restructuring"
CONFIDENCE: 0.7
TTL: 365
IMPORTANCE_BASE: 0.8
```

### 5. Tech Stack Changes
```yaml
CATEGORY: 01_project
TRIGGERS:
  - "added library"
  - "upgraded to"
  - "migrated to"
  - "new dependency"
  - "npm install"
  - "pip install"
CONFIDENCE: 0.8
TTL: 365
IMPORTANCE_BASE: 0.7
```

---

## ❓ ASK_USER Patterns

These patterns trigger a CONFIRMATION prompt:

### 1. Business Logic
```yaml
CATEGORY: 04_domain
TRIGGERS:
  - "business rule"
  - "logic"
  - "requirement"
  - "policy"
PROMPT: "💡 Business rule detected. Save to memory? [y/N]"
```

### 2. Code Snippets
```yaml
CATEGORY: 05_code
TRIGGERS:
  - "code for"
  - "code example"
  - "snippet"
  - "reference code"
PROMPT: "💡 Save code snippet to memory? [y/N]"
```

### 3. Personal Preferences
```yaml
CATEGORY: 13_preferences
TRIGGERS:
  - "I prefer"
  - "I like"
  - "setting"
  - "style choice"
PROMPT: "💡 Save as user preference? [y/N]"
```

---

## ⚙️ Global Settings

```yaml
# Enable/disable auto-save system
AUTO_SAVE_ENABLED: true

# Minimum confidence to trigger auto-save (0.0 - 1.0)
MIN_CONFIDENCE: 0.7

# Show notification when auto-saving
NOTIFY_ON_AUTO_SAVE: true

# Format of notification
NOTIFICATION_FORMAT: "💾 Auto-saved to {category}: {summary}"

# Maximum auto-saves per session (prevent spam)
MAX_AUTO_SAVES_PER_SESSION: 10

# Cooldown between saves of same category (minutes)
CATEGORY_COOLDOWN: 5
```

---

## 🔧 How It Works

1. **AI analyzes** each user message.
2. **Searches for triggers** in the lists above.
3. **If AUTO_SAVE trigger found** → saves + notifies.
4. **If ASK_USER trigger found** → asks for confirmation.
5. **If nothing found** → doesn't save (use /remember manually).

---

## 🎨 Customization

Add your own triggers to the corresponding sections above.

Example:
```yaml
# Add trigger for DevOps
CATEGORY: 11_deployment
TRIGGERS:
  - "docker"
  - "kubernetes"
  - "CI/CD"
CONFIDENCE: 0.8
```
