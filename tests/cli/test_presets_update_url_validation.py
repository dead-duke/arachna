from unittest.mock import patch

import pytest

from arachna.cli.presets import _cmd_presets_update


def _make_args(url=None):
    from argparse import Namespace

    return Namespace(url=url)


def test_presets_update_rejects_file_url(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(ValueError, match="Only https://"):
        _cmd_presets_update(_make_args(url="file:///etc/passwd"), config)


def test_presets_update_rejects_ftp_url(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(ValueError, match="Only https://"):
        _cmd_presets_update(_make_args(url="ftp://evil.com/presets.json"), config)


def test_presets_update_rejects_non_local_http(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(ValueError, match="URL must use https://"):
        _cmd_presets_update(_make_args(url="http://example.com/presets.json"), config)


def test_presets_update_allows_https_url(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    mock_presets = {
        "test": {
            "dirs": ["src"],
            "patterns": ["*.py"],
            "max_tokens": 100,
            "split_mode": "by_file",
            "detect": ["src"],
        }
    }
    with (
        patch("arachna.cli.presets.fetch_presets", return_value=mock_presets),
    ):
        _cmd_presets_update(_make_args(url="https://example.com/presets.json"), config)
