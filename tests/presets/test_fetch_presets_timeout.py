"""Tests for fetch_presets timeout parameter (v3.5.0)."""

from unittest.mock import patch


def test_fetch_presets_timeout_param():
    """fetch_presets accepts explicit timeout parameter."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = TimeoutError("timed out")
        from arachna.presets import fetch_presets

        result = fetch_presets("https://example.com/presets.json", timeout=3)
        assert result == {}
        mock_urlopen.assert_called_with("https://example.com/presets.json", timeout=3)


def test_fetch_presets_timeout_env(monkeypatch):
    """ARACHNA_PRESETS_TIMEOUT env var used as default."""
    monkeypatch.setenv("ARACHNA_PRESETS_TIMEOUT", "5")
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = TimeoutError("timed out")
        from arachna.presets import fetch_presets

        result = fetch_presets("https://example.com/presets.json")
        assert result == {}
        mock_urlopen.assert_called_with("https://example.com/presets.json", timeout=5)


def test_fetch_presets_timeout_default(monkeypatch):
    """Default timeout is 10 seconds."""
    monkeypatch.delenv("ARACHNA_PRESETS_TIMEOUT", raising=False)
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = TimeoutError("timed out")
        from arachna.presets import fetch_presets

        result = fetch_presets("https://example.com/presets.json")
        assert result == {}
        mock_urlopen.assert_called_with("https://example.com/presets.json", timeout=10)
