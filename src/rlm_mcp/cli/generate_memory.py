from __future__ import annotations

from ._repo_scripts import run_repo_script


def main() -> int:
    return run_repo_script("generate_rlm_memory_from_code.py")


if __name__ == "__main__":
    raise SystemExit(main())
