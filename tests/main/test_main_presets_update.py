import json
from unittest.mock import patch

from arachna.cli.presets import _cmd_presets_update


def _make_args(url=None):
    from argparse import Namespace

    return Namespace(url=url)


def test_cmd_presets_update_success(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})

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

    with patch("arachna.cli.presets.fetch_presets", return_value=mock_remote):
        _cmd_presets_update(_make_args(), config)

    assert (tmp_path / "presets.json").exists()
    data = json.loads((tmp_path / "presets.json").read_text())
    assert "go" in data
    assert "python" in data


def test_cmd_presets_update_fetch_fails(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with (
        patch("arachna.cli.presets.fetch_presets", return_value={}),
        patch("sys.exit") as mock_exit,
    ):
        _cmd_presets_update(_make_args(), config)
        mock_exit.assert_called_with(1)


def test_cmd_presets_update_preserves_local(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
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

    with patch("arachna.cli.presets.fetch_presets", return_value=mock_remote):
        _cmd_presets_update(_make_args(), config)

    data = json.loads((tmp_path / "presets.json").read_text())
    assert "my_game" in data
    assert data["my_game"]["dirs"] == ["game"]


def test_cmd_presets_update_with_custom_url(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    mock_remote = {
        "zig": {
            "dirs": ["src"],
            "patterns": ["*.zig"],
            "max_tokens": 16000,
            "split_mode": "by_file",
            "detect": ["build.zig"],
        }
    }

    with patch("arachna.cli.presets.fetch_presets") as mock_fetch:
        mock_fetch.return_value = mock_remote
        _cmd_presets_update(_make_args(url="https://custom.example.com/presets.json"), config)
        mock_fetch.assert_called_with("https://custom.example.com/presets.json")
