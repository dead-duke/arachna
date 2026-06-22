"""Tests for plugin install with PEP668 externally-managed environment."""

from unittest.mock import patch

from arachna.plugins.plugins import install_plugin


def test_install_plugin_pep668_blocked(tmp_path):
    """System Python with PEP668 marker shows options, not pip command."""
    marker = tmp_path / "EXTERNALLY-MANAGED"
    marker.write_text("")
    with (
        patch("arachna.plugins.plugins._is_installed", return_value=False),
        patch("arachna.plugins.plugins._detect_environment", return_value="system"),
        patch("sysconfig.get_path", return_value=str(tmp_path)),
    ):
        result = install_plugin("javascript")
    assert "Cannot install" in result
    assert "PEP 668" in result
    assert "pip install" not in result.split("Options:")[0] if "Options:" in result else True
