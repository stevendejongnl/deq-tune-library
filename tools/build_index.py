"""Writes `site/index.json`, the one file that the app reads.

    uv run python -m tools.build_index

The CI runs it after `tools.check` and publishes `site/` on GitHub Pages.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.library import build_index

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    site = ROOT / "site"
    site.mkdir(exist_ok=True)
    index = build_index(ROOT)
    (site / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")))
    print(f"site/index.json: {len(index['entries'])} entries.")


if __name__ == "__main__":
    main()
