"""Additional coverage for plugins.py — install execute, subprocess error, already installed detection."""

from unittest.mock import patch

from arachna.plugins.plugins import (
    _detect_environment,
    _is_installed,
    install_plugin,
    list_plugins,
    uninstall_plugin,
)


def test_install_plugin_execute_success():
    with (
        patch("arachna.plugins.plugins._is_installed", return_value=False),
        patch("arachna.plugins.plugins._detect_environment", return_value="venv"),
        patch("subprocess.run") as mock_run,
    ):
        result = install_plugin("tiktoken", execute=True)
        assert "Installing" in result
        assert "ready" in result
        mock_run.assert_called_once()


def test_install_plugin_execute_failure():
    import subprocess

    with (
        patch("arachna.plugins.plugins._is_installed", return_value=False),
        patch("arachna.plugins.plugins._detect_environment", return_value="venv"),
        patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "pip")),
    ):
        result = install_plugin("tiktoken", execute=True)
        assert "failed" in result.lower() or "manually" in result.lower()


def test_install_plugin_already_installed_detection():
    with patch("arachna.plugins.plugins._is_installed", return_value=True):
        result = install_plugin("javascript")
        assert "already installed" in result


def test_is_installed_success():
    assert _is_installed("pathlib")


def test_is_installed_not_found():
    assert not _is_installed("nonexistent_package_xyz")


def test_list_plugins_all_have_fields():
    plugins = list_plugins()
    for name, info in plugins.items():
        assert "description" in info, f"Missing description for {name}"
        assert "installed" in info, f"Missing installed for {name}"
        assert "deps" in info, f"Missing deps for {name}"
        assert isinstance(info["installed"], bool)


def test_uninstall_plugin_installed_detection():
    with patch("arachna.plugins.plugins._is_installed", return_value=True):
        result = uninstall_plugin("tiktoken")
        assert "pip uninstall" in result


def test_detect_environment_fallback():
    with (
        patch("sys.prefix", "/usr"),
        patch("sys.base_prefix", "/usr"),
        patch.dict("os.environ", {}, clear=True),
        patch("sys.executable", "/usr/bin/python"),
    ):
        env = _detect_environment()
        assert env == "system"
