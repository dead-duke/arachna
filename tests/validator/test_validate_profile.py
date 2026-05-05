from arachna.validator import validate_profile


def test_valid():
    r = validate_profile("t", {"split_mode": "by_file", "max_tokens": 100, "directories": ["src"]})
    assert r["errors"] == []


def test_invalid_split_mode():
    r = validate_profile("t", {"split_mode": "x", "max_tokens": 100, "directories": ["src"]})
    assert len(r["errors"]) == 1


def test_zero_max_tokens():
    r = validate_profile("t", {"max_tokens": 0, "directories": ["src"]})
    assert len(r["errors"]) == 1


def test_negative_max_tokens():
    r = validate_profile("t", {"max_tokens": -1, "directories": ["src"]})
    assert len(r["errors"]) == 1


def test_by_marker_no_marker():
    r = validate_profile("t", {"split_mode": "by_marker", "max_tokens": 100, "command": "echo"})
    assert any("split_marker" in e for e in r["errors"])


def test_by_marker_with_marker():
    r = validate_profile(
        "t", {"split_mode": "by_marker", "split_marker": "x", "max_tokens": 100, "command": "echo"}
    )
    assert r["errors"] == []


def test_no_source():
    r = validate_profile("t", {"max_tokens": 100})
    assert any("No content source" in e for e in r["errors"])


def test_command_is_source():
    r = validate_profile("t", {"max_tokens": 100, "command": "echo"})
    assert r["errors"] == []


def test_dir_not_found():
    r = validate_profile("t", {"max_tokens": 100, "directories": ["xyz_nonexistent"]})
    assert any("xyz_nonexistent" in w for w in r["warnings"])


def test_file_not_found():
    r = validate_profile("t", {"max_tokens": 100, "files": ["xyz_nonexistent.txt"]})
    assert any("xyz_nonexistent" in w for w in r["warnings"])
