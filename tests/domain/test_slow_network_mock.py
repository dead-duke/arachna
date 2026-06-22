"""Tests for slow network mock in fetch_presets."""

import time
from unittest.mock import patch


def test_fetch_presets_timeout_slow_server():
    """fetch_presets handles slow server with timeout."""

    def slow_urlopen(*args, **kwargs):
        time.sleep(0.5)
        raise TimeoutError("timed out")

    with patch("urllib.request.urlopen", side_effect=slow_urlopen):
        from arachna.config.presets.presets_remote import fetch_presets

        result = fetch_presets("https://slow.example.com/presets.json", timeout=0.1)
    assert result == {}


def test_fetch_presets_timeout_uses_param():
    """fetch_presets uses explicit timeout parameter."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = TimeoutError("timed out")
        from arachna.config.presets.presets_remote import fetch_presets

        result = fetch_presets("https://example.com/presets.json", timeout=5)
        assert result == {}
        mock_urlopen.assert_called_with("https://example.com/presets.json", timeout=5)
