"""Checks every entry of the library. It exits with 1 on a problem.

    uv run python -m tools.check
"""

from __future__ import annotations

import sys
from pathlib import Path

from tools.library import check_library, entry_files, load_checker

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    problems = check_library(ROOT, load_checker(ROOT))
    for problem in problems:
        print(problem)
    if problems:
        print(f"{len(problems)} problems.")
        return 1
    print(f"{len(entry_files(ROOT))} entries, no problems.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
