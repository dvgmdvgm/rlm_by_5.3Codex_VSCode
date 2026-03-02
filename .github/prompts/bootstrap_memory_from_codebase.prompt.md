---
agent: agent
description: Generate RLM memory snapshot from raw codebase using the bootstrap script
---

Run the codebase bootstrap generator script from this repository and create a fresh RLM memory structure for the target project.

## Required behavior

1. Determine target project path:
   - If user explicitly provided a path, use it.
   - Otherwise use current workspace root as target.

2. Run script:

```powershell
python scripts/generate_rlm_memory_from_code.py --project-root "<target_project_path>" --emit-json-graph
```

3. After memory generation, seed canonical memory and run consolidation:

```powershell
python scripts/seed_canonical_from_rlm_memory.py --project-root "<target_project_path>"
```

4. If user requested custom output path, add:

```powershell
--output-dir "<custom_output_dir>"
```

5. If user requested custom graph file, add:

```powershell
--graph-file "<custom_graph_file>"
```

6. After execution, report:
   - generated memory root path,
   - canonical memory files path and item counters,
   - whether `code_graph.json` exists,
   - scan summary (`Scanned files`, framework hints),
   - first-level generated categories.

6. Do not read old memory as source of truth for this operation; this workflow is code-first bootstrap.
