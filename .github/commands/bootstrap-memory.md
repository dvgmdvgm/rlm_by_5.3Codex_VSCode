# /bootstrap-memory

Generate a fresh RLM memory snapshot from codebase using `scripts/generate_rlm_memory_from_code.py`.

## Behavior

1. Resolve target project path:
   - use user-specified path if present,
   - otherwise use active workspace root.
2. Run bootstrap script with JSON graph enabled:
   - `python scripts/generate_rlm_memory_from_code.py --project-root "<target_project_path>" --emit-json-graph`
3. Respect optional user parameters:
   - `--output-dir "..."`
   - `--graph-file "..."`
   - `--max-file-chars ...`
   - `--include-hidden`
4. Return concise execution report:
   - output memory path,
   - graph file path,
   - scanned files count,
   - generated category folders.
