"""Writes entry files into a test's own library directory."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_TUNING_DATA = Path(__file__).with_name("sample_tuning_data.json")


def new_library(directory: Path) -> Path:
    """An empty library with the real schema copy."""
    (directory / "schema").mkdir(parents=True)
    shutil.copy(ROOT / "schema" / "openapi.json", directory / "schema" / "openapi.json")
    return directory


def sample_tuning_data() -> dict:
    return json.loads(SAMPLE_TUNING_DATA.read_text())


def sample_profile(name: str = "Daily", brand: str = "Mazda", model: str = "CX-5") -> dict:
    return {
        "name": name,
        "brand_name": brand,
        "car_model": model,
        "speaker_type": None,
        "supported_processors": [],
        "data": sample_tuning_data(),
    }


def write_file(root: Path, relative_path: str, content: object) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content))
    return path


def write_equalizer(root: Path, slug_name: str, name: str, gains: list[float] | None = None, **extra: object) -> Path:
    entry = {"author": "someone", "description": "A test EQ.", "equalizer": {"name": name, "gains": gains or [0.0] * 13}}
    entry.update(extra)
    return write_file(root, f"equalizers/{slug_name}.json", entry)


def write_profile(root: Path, relative_path: str, profile: dict) -> Path:
    return write_file(root, relative_path, {"author": "someone", "description": "A test profile.", "profile": profile})
