"""Test that presets update writes to the correct root directory."""

import json
from unittest.mock import patch

from arachna.cli.presets import _cmd_presets_update
from arachna.config.core.config import load_config


def _make_args(url=None):
    from argparse import Namespace

    return Namespace(url=url)


def test_presets_update_writes_to_root(tmp_path):
    """presets update writes presets.json to config _root, not cwd."""
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": str(tmp_path / "out"),
                "profiles": {},
            }
        )
    )
    config = load_config(root=tmp_path)
    config._root = str(tmp_path)

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
