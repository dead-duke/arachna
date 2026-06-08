"""Tests for URL validation in --presets-update (v2.9.0 SEC-05)."""

from unittest.mock import patch

from arachna.__main__ import _cmd_presets_update


def test_presets_update_rejects_file_url(tmp_path, monkeypatch):
    """file:// URL is rejected for security reasons."""
    monkeypatch.chdir(tmp_path)

    with patch("sys.exit") as mock_exit:
        _cmd_presets_update(["arachna", "--presets-update", "--url", "file:///etc/passwd"])
        mock_exit.assert_called_with(1)


def test_presets_update_rejects_ftp_url(tmp_path, monkeypatch):
    """Non-http/https URL is rejected."""
    monkeypatch.chdir(tmp_path)

    with patch("sys.exit") as mock_exit:
        _cmd_presets_update(["arachna", "--presets-update", "--url", "ftp://evil.com/presets.json"])
        mock_exit.assert_called_with(1)


def test_presets_update_allows_https_url(tmp_path, monkeypatch):
    """https:// URL passes validation (fetch may fail but not because of URL scheme)."""
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
        patch("arachna.presets.fetch_presets", return_value=mock_presets),
        patch("sys.exit") as mock_exit,
    ):
        _cmd_presets_update(
            ["arachna", "--presets-update", "--url", "https://example.com/presets.json"]
        )
        # Should NOT call sys.exit for valid URL with successful fetch
        mock_exit.assert_not_called()


def test_presets_update_allows_http_url(tmp_path, monkeypatch):
    """http:// URL passes validation."""
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
        patch("arachna.presets.fetch_presets", return_value=mock_presets),
        patch("sys.exit") as mock_exit,
    ):
        _cmd_presets_update(
            ["arachna", "--presets-update", "--url", "http://example.com/presets.json"]
        )
        mock_exit.assert_not_called()
