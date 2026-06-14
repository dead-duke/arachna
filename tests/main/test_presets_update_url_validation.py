from unittest.mock import patch

from arachna.cli.presets import _cmd_presets_update


def _make_args(url=None):
    from argparse import Namespace

    return Namespace(url=url)


def test_presets_update_rejects_file_url(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("sys.exit") as mock_exit:
        _cmd_presets_update(_make_args(url="file:///etc/passwd"), {})
        mock_exit.assert_called_with(1)


def test_presets_update_rejects_ftp_url(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("sys.exit") as mock_exit:
        _cmd_presets_update(_make_args(url="ftp://evil.com/presets.json"), {})
        mock_exit.assert_called_with(1)


def test_presets_update_allows_https_url(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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
        patch("sys.exit") as mock_exit,
    ):
        _cmd_presets_update(_make_args(url="https://example.com/presets.json"), {})
        mock_exit.assert_not_called()


def test_presets_update_allows_http_url(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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
        patch("sys.exit") as mock_exit,
    ):
        _cmd_presets_update(_make_args(url="http://example.com/presets.json"), {})
        mock_exit.assert_not_called()
