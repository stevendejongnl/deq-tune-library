"""Reads, checks and indexes the entries of the community library.

An entry is one JSON file. An EQ lives at `equalizers/<slug>.json`. A car
profile lives at `profiles/<brand>/<model>/<slug>.json`. Each entry holds
its author, a description, and the item itself, in the same shape as the
deq-tune app's backup file (`LibraryEqualizer` or `LibraryProfile`).

The shape comes from `schema/openapi.json`, a copy of the deq-tune
backend's own schema. `tools/update_schema.py` refreshes that copy. The
value ranges come from the deq-tune backend too: the backend clamps to
them, so a value outside them does not do what its author expects.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

INDEX_FORMAT = "deq-tune-community"
INDEX_VERSION = 1

EQUALIZER_DIRECTORY = "equalizers"
PROFILE_DIRECTORY = "profiles"

ENTRY_KEYS = {"author", "description", "equalizer", "profile"}
DESCRIPTION_MAXIMUM_LENGTH = 500

# From the deq-tune backend: `app/equalizers.py`, `app/deq_dsp.py`.
EQUALIZER_GAIN_LIMIT_DB = 12.0
SPEAKER_LEVEL_MINIMUM_DB = -24.0
SPEAKER_LEVEL_MAXIMUM_DB = 10.0
CUTOFF_POSITION_COUNT = 11
SLOPE_MAXIMUM = 4
TIME_ALIGNMENT_MAXIMUM_SPREAD_CM = 350.0


@dataclass(frozen=True)
class Entry:
    """One entry file. `entry_id` is its path without `.json`."""

    entry_id: str
    kind: str
    content: dict


def slug(text: str) -> str:
    """The file or directory name for a name: lower case, words joined by `-`."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def entry_files(root: Path) -> list[Path]:
    files = list((root / EQUALIZER_DIRECTORY).glob("*.json"))
    files += list((root / PROFILE_DIRECTORY).glob("*/*/*.json"))
    return sorted(files)


def stray_files(root: Path) -> list[Path]:
    """JSON files in an entry directory, but not at an entry's place."""
    placed = set(entry_files(root))
    candidates = list((root / EQUALIZER_DIRECTORY).rglob("*.json"))
    candidates += list((root / PROFILE_DIRECTORY).rglob("*.json"))
    return sorted(path for path in candidates if path not in placed)


def entry_kind(root: Path, path: Path) -> str:
    return "equalizer" if path.relative_to(root).parts[0] == EQUALIZER_DIRECTORY else "profile"


def read_entry(root: Path, path: Path) -> Entry:
    entry_id = path.relative_to(root).with_suffix("").as_posix()
    return Entry(entry_id=entry_id, kind=entry_kind(root, path), content=json.loads(path.read_text()))


class EntryChecker:
    """Finds the problems in one entry.

    Call `problems(entry)`. It returns a list of sentences, empty for a good
    entry. It depends on the deq-tune OpenAPI document, for the item shapes.
    """

    def __init__(self, openapi: dict) -> None:
        self.validators = {
            kind: Draft202012Validator(
                {"$ref": f"#/components/schemas/{schema_name}", "components": openapi["components"]}
            )
            for kind, schema_name in (("equalizer", "LibraryEqualizer"), ("profile", "LibraryProfile"))
        }

    def problems(self, entry: Entry) -> list[str]:
        found = self.entry_key_problems(entry)
        if found:
            return found
        item = entry.content[entry.kind]
        found = [
            f"{entry.kind}: {error.message} at {'/'.join(str(part) for part in error.absolute_path) or 'the top'}"
            for error in self.validators[entry.kind].iter_errors(item)
        ]
        if found:
            return found
        if entry.kind == "equalizer":
            return gain_problems(item["gains"], "gains")
        return profile_problems(entry.entry_id, item)

    def entry_key_problems(self, entry: Entry) -> list[str]:
        content = entry.content
        if not isinstance(content, dict):
            return ["the file must hold one JSON object"]
        found = [f"unknown key {key!r}" for key in sorted(set(content) - ENTRY_KEYS)]
        if entry.kind not in content:
            found.append(f"the {entry.kind!r} key is missing")
        other_kind = "profile" if entry.kind == "equalizer" else "equalizer"
        if other_kind in content:
            found.append(f"an entry in this directory holds an {entry.kind}, not a {other_kind}")
        if not text_value(content.get("author")):
            found.append("the author is missing")
        description = content.get("description")
        if not text_value(description):
            found.append("the description is missing")
        elif len(description) > DESCRIPTION_MAXIMUM_LENGTH:
            found.append(f"the description is longer than {DESCRIPTION_MAXIMUM_LENGTH} characters")
        return found


def text_value(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def gain_problems(gains: list[float], where: str) -> list[str]:
    return [
        f"{where}[{band}] is {gain} dB, outside ±{EQUALIZER_GAIN_LIMIT_DB:g} dB"
        for band, gain in enumerate(gains)
        if abs(gain) > EQUALIZER_GAIN_LIMIT_DB
    ]


def profile_problems(entry_id: str, profile: dict) -> list[str]:
    found = profile_place_problems(entry_id, profile)
    data = profile["data"]
    found += speaker_problems(data["speakers"])
    found += filter_problems(data["filter"])
    found += foundation_eq_problems(data["foundationEq"])
    return found


def profile_place_problems(entry_id: str, profile: dict) -> list[str]:
    """A profile's directories name its car, so the list stays sorted by car."""
    brand_name = profile.get("brand_name")
    car_model = profile.get("car_model")
    if not text_value(brand_name) or not text_value(car_model):
        return ["a profile needs its brand_name and its car_model"]
    expected = f"{PROFILE_DIRECTORY}/{slug(brand_name)}/{slug(car_model)}/"
    if not entry_id.startswith(expected):
        return [f"a profile for {brand_name} {car_model} belongs in {expected}"]
    return []


def speaker_problems(speakers: dict) -> list[str]:
    found = [
        f"speaker {name}: level {speaker['levelDB']} dB is outside "
        f"{SPEAKER_LEVEL_MINIMUM_DB:g} to {SPEAKER_LEVEL_MAXIMUM_DB:g} dB"
        for name, speaker in speakers.items()
        if not SPEAKER_LEVEL_MINIMUM_DB <= speaker["levelDB"] <= SPEAKER_LEVEL_MAXIMUM_DB
    ]
    distances = [speaker["timeAlignmentCm"] for speaker in speakers.values()]
    found += [f"speaker {name}: a negative distance" for name, speaker in speakers.items() if speaker["timeAlignmentCm"] < 0]
    if distances and max(distances) - min(distances) > TIME_ALIGNMENT_MAXIMUM_SPREAD_CM:
        found.append(f"the speaker distances spread more than {TIME_ALIGNMENT_MAXIMUM_SPREAD_CM:g} cm")
    return found


def filter_problems(filters: dict) -> list[str]:
    found = []
    for name, band in filters.items():
        if band["cutoff_hpf"] not in range(CUTOFF_POSITION_COUNT):
            found.append(f"filter {name}: cutoff_hpf must be a position from 0 to {CUTOFF_POSITION_COUNT - 1}")
        if band["slope_hpf"] not in range(SLOPE_MAXIMUM + 1):
            found.append(f"filter {name}: slope_hpf must be from 0 to {SLOPE_MAXIMUM}")
    return found


def foundation_eq_problems(foundation_eq: dict) -> list[str]:
    found = []
    for name, bank in foundation_eq["expandEq"].items():
        found += gain_problems(bank["banks"]["gain"], f"foundationEq.expandEq.{name}.gain")
    return found


def duplicate_name_problems(entries: list[Entry]) -> list[str]:
    """Two entries of one kind with one name would look like one in the app."""
    seen: dict[tuple[str, str], str] = {}
    found = []
    for entry in entries:
        key = (entry.kind, entry.content[entry.kind]["name"].strip().lower())
        if key in seen:
            found.append(f"{entry.entry_id}: the name is the same as {seen[key]}")
        seen.setdefault(key, entry.entry_id)
    return found


def check_library(root: Path, checker: EntryChecker) -> list[str]:
    """Every problem in the library, each with the entry it belongs to."""
    found = [f"{path.relative_to(root)}: not at an entry's place" for path in stray_files(root)]
    good_entries = []
    for path in entry_files(root):
        try:
            entry = read_entry(root, path)
        except json.JSONDecodeError as caught_error:
            found.append(f"{path.relative_to(root)}: not valid JSON ({caught_error.msg}, line {caught_error.lineno})")
            continue
        entry_problems = checker.problems(entry)
        found += [f"{entry.entry_id}: {problem}" for problem in entry_problems]
        if not entry_problems:
            good_entries.append(entry)
    return found + duplicate_name_problems(good_entries)


def index_entry(entry: Entry) -> dict:
    """The app adds an entry without a star, so the index drops `favorite`."""
    item = {key: value for key, value in entry.content[entry.kind].items() if key != "favorite"}
    return {
        "id": entry.entry_id,
        "kind": entry.kind,
        "author": entry.content["author"].strip(),
        "description": entry.content["description"].strip(),
        entry.kind: item,
    }


def build_index(root: Path) -> dict:
    entries = [read_entry(root, path) for path in entry_files(root)]
    return {"format": INDEX_FORMAT, "version": INDEX_VERSION, "entries": [index_entry(entry) for entry in entries]}


def load_checker(root: Path) -> EntryChecker:
    return EntryChecker(json.loads((root / "schema" / "openapi.json").read_text()))
