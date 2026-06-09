"""TEST-05: Slow network mock for fetch_presets (v2.9.2)."""

import time
from unittest.mock import patch


def test_fetch_presets_timeout_slow_server(monkeypatch):
    """fetch_presets handles slow server with timeout."""
    monkeypatch.setenv("ARACHNA_PRESETS_TIMEOUT", "1")
    import importlib

    import arachna.presets as presets_module

    importlib.reload(presets_module)

    def slow_urlopen(*args, **kwargs):
        time.sleep(2)
        raise TimeoutError("timed out")

    with patch("urllib.request.urlopen", side_effect=slow_urlopen):
        result = presets_module.fetch_presets("https://slow.example.com/presets.json")
    assert result == {}


def test_fetch_presets_timeout_real_urlopen(monkeypatch):
    """fetch_presets uses configured timeout."""
    monkeypatch.setenv("ARACHNA_PRESETS_TIMEOUT", "5")
    import importlib

    import arachna.presets as presets_module

    importlib.reload(presets_module)

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = TimeoutError("timed out")
        result = presets_module.fetch_presets("https://example.com/presets.json")
        assert result == {}
        mock_urlopen.assert_called_with("https://example.com/presets.json", timeout=5)
