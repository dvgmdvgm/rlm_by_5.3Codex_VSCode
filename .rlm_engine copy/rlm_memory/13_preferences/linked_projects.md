# 🔗 Linked Projects

> Cross-project search configuration for `/recall --global`

---

## 📋 Description

This file defines other projects with RLM-Anchor installed.
When using `/recall --global [query]`, the AI will search these
projects in addition to the current one.

> [!NOTE]
> Only _index.md files are read from linked projects (Level 1 search).
> File contents are read only when a match is found.
> Nothing is ever modified in linked projects.

---

## 📂 Linked Projects

| Project | Path to .agent/ | Description |
|---------|-----------------|-------------|
| — | — | — |

**Example:**

```markdown
| Project | Path to .agent/ | Description |
|---------|-----------------|-------------|
| MyApp | D:/Projects/myapp/.agent | Main web application |
| API-Gateway | D:/Projects/gateway/.agent | API gateway service |
```

---

## ⚙️ Settings

```yaml
# Enable/disable global search
GLOBAL_SEARCH_ENABLED: true

# Maximum projects to search (performance)
MAX_PROJECTS: 5

# Search depth in linked projects
SEARCH_DEPTH: index_only    # index_only | content_too
```

---

## ⚠️ Important

- Paths must be **absolute** and point to the `.agent/` folder
- Each linked project must have `.agent/memory/` inside
- Global search is **opt-in** — only works with `--global` flag
- AI will **never modify** linked project files
