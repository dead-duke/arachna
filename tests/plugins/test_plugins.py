"""Tests for plugin system in plugins.py."""

import os
from unittest.mock import patch

import pytest

from arachna.plugins import (
    _build_install_command,
    _detect_environment,
    _has_pep668,
    _is_installed,
    install_plugin,
    list_plugins,
    uninstall_plugin,
)


def test_detect_environment_pipx():
    with patch.dict(os.environ, {"PIPX_HOME": "/home/user/.local/pipx"}, clear=True):
        assert _detect_environment() == "pipx"


def test_detect_environment_pipx_in_path():
    with (
        patch("sys.executable", "/home/user/.local/pipx/venvs/arachna/bin/python"),
        patch.dict(os.environ, {}, clear=True),
    ):
        assert _detect_environment() == "pipx"


def test_detect_environment_poetry():
    with patch.dict(os.environ, {"POETRY_ACTIVE": "1"}, clear=True):
        assert _detect_environment() == "poetry"


def test_detect_environment_poetry_home():
    with patch.dict(os.environ, {"POETRY_HOME": "/home/user/.poetry"}, clear=True):
        assert _detect_environment() == "poetry"


def test_detect_environment_conda():
    with patch.dict(os.environ, {"CONDA_PREFIX": "/opt/conda"}, clear=True):
        assert _detect_environment() == "conda"


def test_detect_environment_uv(tmp_path):
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("home = /usr/bin")
    with (
        patch("sys.executable", str(venv / "bin" / "python")),
        patch.dict(os.environ, {}, clear=True),
    ):
        assert _detect_environment() == "uv"


def test_detect_environment_venv():
    with (
        patch("sys.prefix", "/home/user/.venv"),
        patch("sys.base_prefix", "/usr"),
        patch.dict(os.environ, {}, clear=True),
    ):
        assert _detect_environment() == "venv"


def test_detect_environment_system():
    with (
        patch("sys.prefix", "/usr"),
        patch("sys.base_prefix", "/usr"),
        patch.dict(os.environ, {}, clear=True),
    ):
        assert _detect_environment() == "system"


def test_pep668_detected(tmp_path):
    marker = tmp_path / "EXTERNALLY-MANAGED"
    marker.write_text("")
    with patch("sysconfig.get_path", return_value=str(tmp_path)):
        assert _has_pep668()


def test_pep668_not_detected(tmp_path):
    with patch("sysconfig.get_path", return_value=str(tmp_path)):
        assert not _has_pep668()


def test_build_install_command_pipx():
    cmd = _build_install_command("javascript", "pipx")
    assert "pipx inject arachna" in cmd
    assert "tree-sitter-javascript" in cmd


def test_build_install_command_venv():
    cmd = _build_install_command("javascript", "venv")
    assert "pip install" in cmd
    assert "tree-sitter-javascript" in cmd


def test_build_install_command_uv():
    cmd = _build_install_command("go", "uv")
    assert "pip install" in cmd
    assert "tree-sitter-go" in cmd


def test_build_install_command_conda():
    cmd = _build_install_command("javascript", "conda")
    assert "pip install" in cmd


def test_build_install_command_poetry():
    cmd = _build_install_command("typescript", "poetry")
    assert "poetry add" in cmd


def test_build_install_command_system_no_pep668(tmp_path):
    with patch("sysconfig.get_path", return_value=str(tmp_path)):
        cmd = _build_install_command("javascript", "system")
        assert cmd is not None
        assert "pip install" in cmd


def test_build_install_command_system_pep668(tmp_path):
    marker = tmp_path / "EXTERNALLY-MANAGED"
    marker.write_text("")
    with patch("sysconfig.get_path", return_value=str(tmp_path)):
        cmd = _build_install_command("javascript", "system")
        assert cmd is None


def test_build_install_command_unknown_language():
    assert _build_install_command("nonexistent", "venv") is None


def test_list_plugins():
    plugins = list_plugins()
    assert "javascript" in plugins
    assert "typescript" in plugins
    assert "go" in plugins
    assert "tiktoken" in plugins
    for info in plugins.values():
        assert "description" in info
        assert "installed" in info
        assert "deps" in info


def test_install_plugin_unknown():
    result = install_plugin("nonexistent")
    assert "Unknown plugin" in result


@pytest.mark.skipif(not _is_installed("tree_sitter"), reason="tree_sitter not installed")
def test_install_plugin_already_installed():
    result = install_plugin("javascript")
    assert "already installed" in result


def test_uninstall_plugin_unknown():
    result = uninstall_plugin("nonexistent")
    assert "Unknown plugin" in result


def test_is_installed_builtin():
    assert _is_installed("pathlib")


def test_is_installed_nonexistent():
    assert not _is_installed("nonexistent_package_xyz")


@pytest.mark.skipif(not _is_installed("tree_sitter"), reason="tree_sitter not installed")
def test_is_installed_tree_sitter():
    assert _is_installed("tree_sitter")
