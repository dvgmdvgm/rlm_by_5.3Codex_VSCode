# 🧠 Memory Settings

> **Configures the behavior of the memory system.**
> **Modified**: 2026-02-27 (Translated to EN)

---

## 💾 Auto-Save Behavior

Controls whether the AI saves important information automatically or asks for confirmation first.

```
AUTO_SAVE=ask
```

**Options:**
- `ask` (Recommended) - The AI will ask: "Should I save this?" (Highest data quality).
- `auto` - The AI will save without asking (May accumulate noise).

---

## 🔔 Notifications

Controls whether the AI provides a visual confirmation when data is saved.

```
NOTIFY_ON_SAVE=true
```

**Options:**
- `true` - Always confirms: "💾 Saved to..."
- `false` - Saves silently.

---

## 📊 Note on Stability

For RLM (Recursive Language Models), **Quality > Quantity**.
Using `AUTO_SAVE=ask` ensures that only truly valuable information enters long-term memory, keeping search results fast and accurate.
