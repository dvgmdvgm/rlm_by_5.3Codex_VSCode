from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (project_root / path).resolve()


def generate_run_layout(project_root: Path, tasks_root: Path, prefix: str) -> dict[str, str]:
    timestamp = _utc_now().strftime("%Y%m%d_%H%M%S")
    base_run_id = f"{prefix}_{timestamp}"
    run_id = base_run_id
    suffix = 1

    while (tasks_root / run_id).exists():
        suffix += 1
        run_id = f"{base_run_id}_{suffix:02d}"

    run_dir = tasks_root / run_id
    return {
        "run_id": run_id,
        "run_dir": run_dir.as_posix(),
        "tasks_root": tasks_root.as_posix(),
        "state_file": (run_dir / "orchestrator_state.json").as_posix(),
        "master_plan_file": (run_dir / "master_plan.md").as_posix(),
        "validation_report_file": (run_dir / "validation_report.json").as_posix(),
        "audit_log_file": (run_dir / "orchestration_audit.jsonl").as_posix(),
        "created_at": _utc_now().isoformat(),
        "format": "<prefix>_YYYYMMDD_HHMMSS[_NN]",
        "project_root": project_root.as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a unique per-run orchestration directory layout."
    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument(
        "--tasks-root",
        default=".vscode/tasks",
        help="Tasks root directory relative to project root",
    )
    parser.add_argument(
        "--prefix",
        default="orch",
        help="Run ID prefix. Result format: <prefix>_YYYYMMDD_HHMMSS[_NN]",
    )
    parser.add_argument(
        "--create-dir",
        action="store_true",
        help="Create the run directory immediately",
    )
    parser.add_argument(
        "--output-format",
        choices=("json", "text"),
        default="json",
        help="Output format",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    tasks_root = _resolve_path(project_root, args.tasks_root)
    tasks_root.mkdir(parents=True, exist_ok=True)

    layout = generate_run_layout(project_root, tasks_root, args.prefix)
    if args.create_dir:
        Path(layout["run_dir"]).mkdir(parents=True, exist_ok=False)

    if args.output_format == "json":
        print(json.dumps(layout, ensure_ascii=False, indent=2))
    else:
        for key in (
            "run_id",
            "run_dir",
            "state_file",
            "master_plan_file",
            "validation_report_file",
            "audit_log_file",
            "format",
        ):
            print(f"{key}={layout[key]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
