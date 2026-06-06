"""Tests for --presets-update CLI handler in __main__.py (v2.4.0)."""

import json
from unittest.mock import patch

from arachna.__main__ import _cmd_presets_update


def test_cmd_presets_update_success(tmp_path, monkeypatch):
    """--presets-update fetches remote, merges, writes presets.json."""
    monkeypatch.chdir(tmp_path)

    mock_remote = {
        "go": {
            "dirs": ["."],
            "patterns": ["*.go"],
            "files": ["go.mod"],
            "max_tokens": 16000,
            "split_mode": "by_file",
            "detect": ["go.mod"],
        }
    }

    with patch("arachna.presets.fetch_presets", return_value=mock_remote):
        _cmd_presets_update(["arachna", "--presets-update"])

    assert (tmp_path / "presets.json").exists()
    data = json.loads((tmp_path / "presets.json").read_text())
    assert "go" in data
    assert "python" in data  # built-in preserved


def test_cmd_presets_update_fetch_fails(tmp_path, monkeypatch):
    """--presets-update exits 1 when fetch returns empty."""
    monkeypatch.chdir(tmp_path)

    with (
        patch("arachna.presets.fetch_presets", return_value={}),
        patch("sys.exit") as mock_exit,
    ):
        _cmd_presets_update(["arachna", "--presets-update"])
        mock_exit.assert_called_with(1)


def test_cmd_presets_update_preserves_local(tmp_path, monkeypatch):
    """--presets-update does not overwrite existing local presets."""
    monkeypatch.chdir(tmp_path)

    # Pre-existing local preset
    local_presets = {
        "my_game": {
            "dirs": ["game"],
            "patterns": ["*.lua"],
            "max_tokens": 8000,
            "split_mode": "by_file",
            "detect": ["game"],
        }
    }
    (tmp_path / "presets.json").write_text(json.dumps(local_presets))

    mock_remote = {
        "go": {
            "dirs": ["."],
            "patterns": ["*.go"],
            "files": ["go.mod"],
            "max_tokens": 16000,
            "split_mode": "by_file",
            "detect": ["go.mod"],
        }
    }

    with patch("arachna.presets.fetch_presets", return_value=mock_remote):
        _cmd_presets_update(["arachna", "--presets-update"])

    data = json.loads((tmp_path / "presets.json").read_text())
    assert "my_game" in data  # local preserved
    assert data["my_game"]["dirs"] == ["game"]


def test_cmd_presets_update_with_custom_url(tmp_path, monkeypatch):
    """--presets-update --url overrides default URL."""
    monkeypatch.chdir(tmp_path)

    mock_remote = {
        "zig": {
            "dirs": ["src"],
            "patterns": ["*.zig"],
            "max_tokens": 16000,
            "split_mode": "by_file",
            "detect": ["build.zig"],
        }
    }

    with patch("arachna.presets.fetch_presets") as mock_fetch:
        mock_fetch.return_value = mock_remote
        _cmd_presets_update(
            ["arachna", "--presets-update", "--url", "https://custom.example.com/presets.json"]
        )
        mock_fetch.assert_called_with("https://custom.example.com/presets.json")
