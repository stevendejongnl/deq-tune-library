"""Copies the deq-tune backend's schema to `schema/openapi.json`.

    uv run python -m tools.update_schema

Run it when deq-tune changes the shape of its backup file. Then run
`tools.check`: an entry that the new shape refuses needs a fix.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

SCHEMA_URL = "https://raw.githubusercontent.com/stevendejongnl/deq-tune/main/openapi.json"
ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    with urllib.request.urlopen(SCHEMA_URL, timeout=30) as response:
        (ROOT / "schema" / "openapi.json").write_bytes(response.read())
    print("schema/openapi.json updated.")


if __name__ == "__main__":
    main()
