"""Makes an entry from one item of a deq-tune backup file.

Save a backup in the app (Settings → Backup → Save to a file). Then name
the EQ or the profile to share:

    uv run python -m tools.add_entry deq-tune-library-2026-10-24.json \\
        --equalizer "Night drive" --author your-github-name \\
        --description "Less bass and softer highs, for the motorway at night."

    uv run python -m tools.add_entry deq-tune-library-2026-10-24.json \\
        --profile "My CX-5" --author your-github-name \\
        --description "Mazda CX-5 2019, Bose. Timing measured from the driver's seat."

It writes the entry at its place and prints the path. It refuses to
overwrite an entry that is there. A profile needs its brand and car model
in the backup file. `--brand` and `--model` set them when they are missing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.library import EQUALIZER_DIRECTORY, PROFILE_DIRECTORY, slug

ROOT = Path(__file__).resolve().parent.parent


class EntryError(Exception):
    """A request that the backup file cannot fill."""


def find_item(items: list[dict], name: str, kind: str) -> dict:
    for item in items:
        if item["name"] == name:
            return item
    names = ", ".join(repr(item["name"]) for item in items) or "none"
    raise EntryError(f"the backup file has no {kind} named {name!r}. It has: {names}")


def equalizer_entry(backup: dict, name: str) -> tuple[str, dict]:
    item = find_item(backup.get("equalizers", []), name, "EQ")
    return f"{EQUALIZER_DIRECTORY}/{slug(name)}.json", {"name": item["name"], "gains": item["gains"]}


def profile_entry(backup: dict, name: str, brand: str | None, model: str | None) -> tuple[str, dict]:
    item = dict(find_item(backup.get("profiles", []), name, "profile"))
    item.pop("favorite", None)
    item["brand_name"] = brand or item.get("brand_name")
    item["car_model"] = model or item.get("car_model")
    if not item["brand_name"] or not item["car_model"]:
        raise EntryError("the profile has no brand or car model. Give them with --brand and --model")
    path = f"{PROFILE_DIRECTORY}/{slug(item['brand_name'])}/{slug(item['car_model'])}/{slug(name)}.json"
    return path, item


def write_entry(root: Path, relative_path: str, kind: str, item: dict, author: str, description: str) -> Path:
    path = root / relative_path
    if path.exists():
        raise EntryError(f"{relative_path} is there already. Choose another name")
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"author": author, "description": description, kind: item}
    path.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")
    return path


def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Makes a library entry from a deq-tune backup file.")
    parser.add_argument("backup_file", type=Path)
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--equalizer", help="the name of the EQ to share")
    which.add_argument("--profile", help="the name of the car profile to share")
    parser.add_argument("--author", required=True, help="your GitHub name")
    parser.add_argument("--description", required=True)
    parser.add_argument("--brand", help="the car's brand, for a profile")
    parser.add_argument("--model", help="the car's model, for a profile")
    return parser.parse_args(arguments)


def main(arguments: list[str], root: Path = ROOT) -> int:
    options = parse_arguments(arguments)
    backup = json.loads(options.backup_file.read_text())
    try:
        if options.equalizer is not None:
            relative_path, item = equalizer_entry(backup, options.equalizer)
            kind = "equalizer"
        else:
            relative_path, item = profile_entry(backup, options.profile, options.brand, options.model)
            kind = "profile"
        path = write_entry(root, relative_path, kind, item, options.author, options.description)
    except EntryError as caught_error:
        print(caught_error, file=sys.stderr)
        return 1
    print(path.relative_to(root))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
