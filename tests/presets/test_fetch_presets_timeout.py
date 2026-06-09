"""Tests for ARACHNA_PRESETS_TIMEOUT env var (v2.9.2)."""

from unittest.mock import patch


def test_fetch_presets_timeout_env(monkeypatch):
    """ARACHNA_PRESETS_TIMEOUT overrides default timeout."""
    monkeypatch.setenv("ARACHNA_PRESETS_TIMEOUT", "5")

    import importlib

    import arachna.presets as presets_module

    importlib.reload(presets_module)

    assert presets_module._PRESETS_TIMEOUT == 5


def test_fetch_presets_timeout_default(monkeypatch):
    """Default timeout is 10 seconds."""
    monkeypatch.delenv("ARACHNA_PRESETS_TIMEOUT", raising=False)

    import importlib

    import arachna.presets as presets_module

    importlib.reload(presets_module)

    assert presets_module._PRESETS_TIMEOUT == 10


def test_fetch_presets_timeout_used(monkeypatch):
    """fetch_presets passes timeout to urlopen."""
    monkeypatch.setenv("ARACHNA_PRESETS_TIMEOUT", "3")

    import importlib

    import arachna.presets as presets_module

    importlib.reload(presets_module)

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.read.return_value = b"{}"
        presets_module.fetch_presets("https://example.com/presets.json")
        mock_urlopen.assert_called_with("https://example.com/presets.json", timeout=3)
