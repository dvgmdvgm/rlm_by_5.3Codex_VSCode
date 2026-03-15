from __future__ import annotations

"""Deploy the Antigravity-first workflow layer from this repo into another project.

Managed assets:
- root GEMINI.md bridge
- .agent/
- scripts/rlm/sync_gemini_workflows.py

Deployment behavior:
1. Write a root GEMINI bridge that redirects loaders into `.agent/`
2. Mirror `.agent/` into the target project
3. Remove legacy `.gemini/` and `.agents/` trees from the target project
"""

import argparse
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANAGED_FILES = [Path("scripts/rlm/sync_gemini_workflows.py")]
MANAGED_DIRS = [Path(".agent")]
PRUNED_TARGET_DIRS = [Path(".gemini"), Path(".agents")]
IGNORE_NAMES = shutil.ignore_patterns("__pycache__", ".DS_Store")


def _build_gemini_bridge_text() -> str:
    return """# GEMINI.md - Antigravity bridge\n\nThis project uses the Antigravity-first workflow layout.\n\n## Primary workflow root\n\nUse `.agent/` as the single source of truth:\n\n- `.agent/README.md`\n- `.agent/workflows/orchestrate.md`\n- `.agent/workflows/bootstrap-memory.md`\n- `.agent/workflows/save-memory-rule.md`\n- `.agent/skills/*.md`\n\n## Compatibility note\n\nLegacy `.gemini/` and `.agents/` trees are intentionally omitted in this deployment.\nIf a Gemini-aware loader enters through `GEMINI.md`, redirect it to `.agent/README.md` and then resolve workflows from `.agent/workflows/`.\n\n## Bootstrap rule\n\nBefore work, call `local_memory_bootstrap(question=<user_task>, project_path=<workspace_root>)` and follow the brief.\n"""


def _copy_file(src: Path, dst: Path, dry_run: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"DRY-RUN file: {src} -> {dst}")
        return
    shutil.copy2(src, dst)
    print(f"Copied file: {src} -> {dst}")


def _write_text(dst: Path, content: str, dry_run: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"DRY-RUN text: {dst}")
        return
    dst.write_text(content, encoding="utf-8")
    print(f"Wrote file: {dst}")


def _replace_tree(src: Path, dst: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"DRY-RUN mirror: {src} -> {dst}")
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=IGNORE_NAMES)
    print(f"Mirrored dir: {src} -> {dst}")


def _remove_path(path: Path, dry_run: bool) -> None:
    if not path.exists():
        return
    if dry_run:
        print(f"DRY-RUN remove: {path}")
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    print(f"Removed: {path}")

def deploy_to_project(
    repo_root: Path,
    target_root: Path,
    dry_run: bool = False,
) -> None:
    target_root.mkdir(parents=True, exist_ok=True)

    for rel_file in MANAGED_FILES:
        _copy_file(repo_root / rel_file, target_root / rel_file, dry_run=dry_run)

    _write_text(target_root / Path("GEMINI.md"), _build_gemini_bridge_text(), dry_run=dry_run)

    for rel_dir in MANAGED_DIRS:
        _replace_tree(repo_root / rel_dir, target_root / rel_dir, dry_run=dry_run)

    for rel_dir in PRUNED_TARGET_DIRS:
        _remove_path(target_root / rel_dir, dry_run=dry_run)



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy the Antigravity-first workflow layer to another project.",
    )
    parser.add_argument(
        "--target-project",
        type=Path,
        help="Optional target project root where Gemini workflow assets should be copied.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without writing files.",
    )
    parser.add_argument(
        "--antigravity-clean",
        action="store_true",
        help="Deprecated: clean Antigravity deployment is now the default behavior.",
    )
    return parser.parse_args()



def main() -> int:
    args = parse_args()
    repo_root = REPO_ROOT

    if args.target_project:
        print(f"Deploying Antigravity workflow assets to {args.target_project} ...")
        deploy_to_project(
            repo_root,
            args.target_project,
            dry_run=args.dry_run,
        )

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
