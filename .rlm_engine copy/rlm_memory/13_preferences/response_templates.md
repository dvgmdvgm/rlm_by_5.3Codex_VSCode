# 📋 Response Templates

> **Standard patterns for common response types.**
> **Use these templates to maintain consistency across AI models.**

---

## 1️⃣ Analysis Response

Use when: Analyzing a problem, comparing options, investigating issues.

```markdown
## 🔍 Analysis: [Topic]

### Problem Statement
[1-2 sentences describing the issue]

---

### 📊 Findings

| Aspect | Observation |
|--------|-------------|
| ... | ... |

---

### 💡 Recommendations

1. [First recommendation]
2. [Second recommendation]

---

### ✅ Next Steps
- [ ] Action 1
- [ ] Action 2
```

---

## 2️⃣ Implementation Report

Use when: After completing code changes, feature implementation.

```markdown
## ✅ Implementation Complete: [Feature Name]

### 📁 Changes Made

| File | Change |
|------|--------|
| `file.py` | Added function X |
| `style.css` | Updated layout |

---

### 🔧 How It Works

[Brief explanation of implementation]

---

### 📝 Usage Example

```python
# Example code
```

---

### ⚠️ Notes
- [Any caveats or important info]
```

---

## 3️⃣ Error Explanation

Use when: Explaining an error, debugging issue, troubleshooting.

```markdown
## ❌ Error: [Error Name/Type]

### 🐛 What Happened
[Description of the error]

### 🔍 Root Cause
[Why this error occurred]

---

### ✅ Solution

**Option 1**: [Solution description]
```code
fix_code()
```

**Option 2**: [Alternative solution]

---

### 🛡️ Prevention
[How to avoid this in the future]
```

---

## 4️⃣ Decision Summary

Use when: Recording an architectural decision, choice made.

```markdown
## ⚖️ Decision: [Topic]

### Context
[Why we needed to make this decision]

### Decision
**We chose**: [Choice made]

### Rationale
1. [Reason 1]
2. [Reason 2]

### Alternatives Considered
- [Alt 1] — rejected because [reason]
- [Alt 2] — rejected because [reason]

---

### 📌 Record to memory?
Should I save this decision to `memory/03_decisions/`?
```

---

## 5️⃣ Quick Answer

Use when: Simple question, straightforward answer.

```markdown
## 💡 [Short Answer Title]

[Direct answer in 2-4 lines]

**Example**:
```code
example_here()
```

Need more details? [Offer to elaborate]
```

---

## 6️⃣ Step-by-Step Guide

Use when: Tutorial, how-to, process explanation.

```markdown
## 📝 How to: [Task Name]

### Prerequisites
- [Requirement 1]
- [Requirement 2]

---

### Steps

**Step 1**: [Title]
```code
code_for_step_1()
```

**Step 2**: [Title]
[Instructions]

**Step 3**: [Title]
[Instructions]

---

### ✅ Result
[What user should see/have after completing]

### ⚠️ Common Issues
| Issue | Solution |
|-------|----------|
| ... | ... |
```

---

## 7️⃣ Comparison Response

Use when: Comparing technologies, approaches, options.

```markdown
## 📊 Comparison: [Option A] vs [Option B]

| Criteria | Option A | Option B |
|----------|----------|----------|
| Feature 1 | ✅ | ❌ |
| Feature 2 | ⚠️ Partial | ✅ |
| Performance | 🟢 Fast | 🟡 Medium |

---

### 💡 Recommendation

**For your case**: [Recommendation with reasoning]

---

### When to Choose A:
- [Scenario 1]
- [Scenario 2]

### When to Choose B:
- [Scenario 1]
- [Scenario 2]
```

---

## 8️⃣ Handoff Summary

Use when: Switching models, creating context transfer.

```markdown
## 🔄 Session Handoff

### 📍 Current State
- Working on: [task]
- Last action: [what was done]
- Next step: [what to do]

### 📁 Key Files
- `file1.py` — [purpose]
- `file2.html` — [purpose]

### ⚖️ Recent Decisions
- [Decision 1]
- [Decision 2]

### ⚠️ Important Notes
- [Critical info 1]
- [Critical info 2]

### 📋 Pending Tasks
- [ ] Task 1
- [ ] Task 2
```
