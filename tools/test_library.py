from pathlib import Path

import pytest

from tools.library import build_index, check_library, load_checker, slug
from tools.testing.entries import new_library, sample_profile, write_equalizer, write_file, write_profile


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return new_library(tmp_path)


def problems(root: Path) -> list[str]:
    return check_library(root, load_checker(root))


def test_the_real_library_has_no_problems() -> None:
    real_root = Path(__file__).resolve().parent.parent
    assert problems(real_root) == []


def test_a_good_equalizer_and_profile_have_no_problems(root: Path) -> None:
    write_equalizer(root, "night-drive", "Night drive", [1.0] * 13)
    write_profile(root, "profiles/mazda/cx-5/daily.json", sample_profile())

    assert problems(root) == []


def test_a_gain_beyond_12_db_is_a_problem(root: Path) -> None:
    write_equalizer(root, "loud", "Loud", [13.0] + [0.0] * 12)

    assert problems(root) == ["equalizers/loud: gains[0] is 13.0 dB, outside ±12 dB"]


def test_twelve_bands_do_not_fit_the_schema(root: Path) -> None:
    write_equalizer(root, "short", "Short", [0.0] * 12)

    assert len(problems(root)) == 1
    assert "equalizers/short: equalizer:" in problems(root)[0]


def test_an_entry_needs_its_author_and_description(root: Path) -> None:
    write_file(root, "equalizers/bare.json", {"equalizer": {"name": "Bare", "gains": [0.0] * 13}})

    assert problems(root) == ["equalizers/bare: the author is missing", "equalizers/bare: the description is missing"]


def test_an_unknown_key_is_a_problem(root: Path) -> None:
    write_equalizer(root, "typo", "Typo", descripton="oops")

    assert problems(root) == ["equalizers/typo: unknown key 'descripton'"]


def test_a_profile_in_another_cars_directory_is_a_problem(root: Path) -> None:
    write_profile(root, "profiles/mazda/cx-3/daily.json", sample_profile())

    assert problems(root) == ["profiles/mazda/cx-3/daily: a profile for Mazda CX-5 belongs in profiles/mazda/cx-5/"]


def test_a_speaker_level_beyond_the_range_is_a_problem(root: Path) -> None:
    profile = sample_profile()
    profile["data"]["speakers"]["FL"]["levelDB"] = 11
    write_profile(root, "profiles/mazda/cx-5/daily.json", profile)

    assert problems(root) == ["profiles/mazda/cx-5/daily: speaker FL: level 11 dB is outside -24 to 10 dB"]


def test_a_wide_distance_spread_is_a_problem(root: Path) -> None:
    profile = sample_profile()
    profile["data"]["speakers"]["FL"]["timeAlignmentCm"] = 500
    write_profile(root, "profiles/mazda/cx-5/daily.json", profile)

    assert problems(root) == ["profiles/mazda/cx-5/daily: the speaker distances spread more than 350 cm"]


def test_a_cutoff_position_beyond_the_table_is_a_problem(root: Path) -> None:
    profile = sample_profile()
    profile["data"]["filter"]["front"]["cutoff_hpf"] = 11
    write_profile(root, "profiles/mazda/cx-5/daily.json", profile)

    assert problems(root) == ["profiles/mazda/cx-5/daily: filter front: cutoff_hpf must be a position from 0 to 10"]


def test_two_equalizers_with_one_name_are_a_problem(root: Path) -> None:
    write_equalizer(root, "night", "Night drive")
    write_equalizer(root, "night-drive", "night drive ")

    assert problems(root) == ["equalizers/night: the name is the same as equalizers/night-drive"]


def test_a_file_outside_an_entrys_place_is_a_problem(root: Path) -> None:
    write_file(root, "profiles/mazda/daily.json", {})

    assert problems(root) == ["profiles/mazda/daily.json: not at an entry's place"]


def test_broken_json_is_a_problem(root: Path) -> None:
    (root / "equalizers").mkdir()
    (root / "equalizers" / "broken.json").write_text("{")

    assert problems(root)[0].startswith("equalizers/broken.json: not valid JSON")


def test_the_index_holds_each_entry_without_its_star(root: Path) -> None:
    write_equalizer(root, "night-drive", "Night drive", [1.0] * 13)
    write_file(
        root,
        "equalizers/starred.json",
        {"author": " someone ", "description": "x", "equalizer": {"name": "Starred", "favorite": True, "gains": [0.0] * 13}},
    )

    index = build_index(root)

    assert index["format"] == "deq-tune-community"
    assert [entry["id"] for entry in index["entries"]] == ["equalizers/night-drive", "equalizers/starred"]
    assert index["entries"][1] == {
        "id": "equalizers/starred",
        "kind": "equalizer",
        "author": "someone",
        "description": "x",
        "equalizer": {"name": "Starred", "gains": [0.0] * 13},
    }


def test_slug_joins_words_with_dashes() -> None:
    assert slug("Mazda CX-5 (2019)") == "mazda-cx-5-2019"
