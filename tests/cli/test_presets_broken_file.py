"""Tests for presets update with broken local presets.json."""

from unittest.mock import patch

from arachna.cli.presets import _cmd_presets_update


def _make_args(url=None):
    from argparse import Namespace

    return Namespace(url=url)


def test_presets_update_broken_local_file(tmp_path, make_config):
    """Corrupted local presets.json exits 1 with warning."""
    config = make_config(tmp_path, profiles={})
    (tmp_path / "presets.json").write_text("{invalid json")
    with patch("sys.exit") as mock_exit:
        _cmd_presets_update(_make_args(), config)
        mock_exit.assert_called_with(1)
