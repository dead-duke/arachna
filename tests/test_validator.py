"""Tests for config validator."""

from arachna.validator import validate_profile


def test_valid_profile():
    result = validate_profile(
        "test",
        {
            "split_mode": "by_file",
            "max_tokens": 16000,
            "directories": ["src"],
        },
    )
    assert result["errors"] == []
    assert result["warnings"] == []


def test_invalid_split_mode():
    result = validate_profile(
        "test",
        {
            "split_mode": "by_line",
            "max_tokens": 100,
            "directories": ["src"],
        },
    )
    assert len(result["errors"]) == 1
    assert "split_mode" in result["errors"][0]


def test_invalid_max_tokens():
    result = validate_profile(
        "test",
        {
            "max_tokens": 0,
            "directories": ["src"],
        },
    )
    assert len(result["errors"]) == 1
    assert "max_tokens" in result["errors"][0]


def test_negative_max_tokens():
    result = validate_profile(
        "test",
        {
            "max_tokens": -100,
            "directories": ["src"],
        },
    )
    assert len(result["errors"]) == 1


def test_by_marker_requires_split_marker():
    result = validate_profile(
        "test",
        {
            "split_mode": "by_marker",
            "max_tokens": 100,
            "command": "echo hello",
        },
    )
    assert any("split_marker" in e for e in result["errors"])


def test_by_marker_with_marker_is_valid():
    result = validate_profile(
        "test",
        {
            "split_mode": "by_marker",
            "split_marker": "\n\n===",
            "max_tokens": 100,
            "command": "echo hello",
        },
    )
    assert len(result["errors"]) == 0


def test_no_content_source():
    result = validate_profile(
        "test",
        {
            "max_tokens": 100,
        },
    )
    assert any("No content source" in e for e in result["errors"])


def test_command_satisfies_content_source():
    result = validate_profile(
        "test",
        {
            "max_tokens": 100,
            "command": "echo hello",
        },
    )
    assert len(result["errors"]) == 0


def test_directory_not_found_warning():
    result = validate_profile(
        "test",
        {
            "max_tokens": 100,
            "directories": ["nonexistent_dir_xyz"],
        },
    )
    assert any("nonexistent_dir_xyz" in w for w in result["warnings"])


def test_file_not_found_warning():
    result = validate_profile(
        "test",
        {
            "max_tokens": 100,
            "files": ["nonexistent_file_xyz.txt"],
        },
    )
    assert any("nonexistent_file_xyz" in w for w in result["warnings"])
