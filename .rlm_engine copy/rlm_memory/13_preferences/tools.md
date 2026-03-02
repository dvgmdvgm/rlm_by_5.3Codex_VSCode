# 🛠️ Preferred Tools

- **Date**: 2026-02-09
- **Tags**: tools, terminal, Windows
- **Modified**: 2026-02-27 (Translated to EN)

---

## Terminal Rules

### ❌ DO NOT use Unix-specific commands on Windows

Unix utilities (`du`, `wc`, `find`, `grep`, `sed`, `awk`, etc.) behave **unpredictably** on Windows:
- They may hang on paths containing spaces.
- `du -sk` might never complete execution.
- `/dev/null` is not a valid device in CMD or PowerShell.
- Git Bash emulation is unreliable for agentic workflows.

### ✅ Windows (PowerShell) Alternatives

| Unix Command | Windows Recommendation (PowerShell) |
|--------------|--------------------------------------|
| `du -sk folder/` | `(Get-ChildItem -Recurse 'folder' \| Measure-Object -Property Length -Sum).Sum / 1KB` |
| `find . -name "*.md" \| wc -l` | `(Get-ChildItem -Recurse -Filter '*.md').Count` |
| `grep -r "text" folder/` | **ALWAYS** use the built-in `grep_search` tool |
| `cat file.txt` | **ALWAYS** use the built-in `view_file` tool |

### 💡 Core Principle

Always prioritize using the **built-in agent tools** (`view_file`, `grep_search`, `find_by_name`, `list_dir`) over shell commands whenever possible. They are more reliable and optimized for the agent's context.
