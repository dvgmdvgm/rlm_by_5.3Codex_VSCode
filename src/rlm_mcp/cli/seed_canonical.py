from __future__ import annotations

from ._repo_scripts import run_repo_script


def main() -> int:
    return run_repo_script("seed_canonical_from_rlm_memory.py")


if __name__ == "__main__":
    raise SystemExit(main())
