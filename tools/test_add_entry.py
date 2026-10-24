import json
from pathlib import Path

import pytest

from tools.add_entry import main
from tools.library import check_library, load_checker
from tools.testing.entries import new_library, sample_profile


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return new_library(tmp_path / "library")


def backup_file(directory: Path, profile: dict | None = None) -> Path:
    path = directory / "backup.json"
    path.write_text(
        json.dumps(
            {
                "format": "deq-tune-library",
                "version": 1,
                "profiles": [{**(profile or sample_profile()), "favorite": True}],
                "equalizers": [{"name": "Night drive", "favorite": True, "gains": [1.0] * 13}],
                "starred_factory_profiles": [],
                "starred_factory_equalizers": [],
            }
        )
    )
    return path


def test_an_equalizer_from_a_backup_becomes_a_good_entry(root: Path, tmp_path: Path, capsys) -> None:
    exit_code = main(
        [str(backup_file(tmp_path)), "--equalizer", "Night drive", "--author", "someone", "--description", "Calm."],
        root,
    )

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "equalizers/night-drive.json"
    entry = json.loads((root / "equalizers" / "night-drive.json").read_text())
    assert entry == {"author": "someone", "description": "Calm.", "equalizer": {"name": "Night drive", "gains": [1.0] * 13}}
    assert check_library(root, load_checker(root)) == []


def test_a_profile_lands_in_its_cars_directory(root: Path, tmp_path: Path) -> None:
    main([str(backup_file(tmp_path)), "--profile", "Daily", "--author", "someone", "--description", "Bose."], root)

    entry = json.loads((root / "profiles" / "mazda" / "cx-5" / "daily.json").read_text())
    assert "favorite" not in entry["profile"]
    assert check_library(root, load_checker(root)) == []


def test_a_profile_without_a_car_takes_brand_and_model(root: Path, tmp_path: Path) -> None:
    profile = sample_profile(brand=None, model=None)
    arguments = [str(backup_file(tmp_path, profile)), "--profile", "Daily", "--author", "a", "--description", "b"]

    assert main(arguments, root) == 1
    assert main([*arguments, "--brand", "Mazda", "--model", "MX-5"], root) == 0
    assert (root / "profiles" / "mazda" / "mx-5" / "daily.json").exists()


def test_an_unknown_name_lists_the_names_there(root: Path, tmp_path: Path, capsys) -> None:
    exit_code = main([str(backup_file(tmp_path)), "--equalizer", "Nope", "--author", "a", "--description", "b"], root)

    assert exit_code == 1
    assert "It has: 'Night drive'" in capsys.readouterr().err


def test_it_does_not_overwrite_an_entry(root: Path, tmp_path: Path) -> None:
    arguments = [str(backup_file(tmp_path)), "--equalizer", "Night drive", "--author", "a", "--description", "b"]

    assert main(arguments, root) == 0
    assert main(arguments, root) == 1
