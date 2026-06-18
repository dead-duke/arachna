"""Tests for cli/plugins.py handlers."""

import sys
from argparse import ArgumentParser, Namespace
from io import StringIO

import pytest

from arachna.cli.plugins import (
    _cmd_plugins_install,
    _cmd_plugins_list,
    _cmd_plugins_uninstall,
    _dispatch_plugins,
)
from arachna.plugins.plugins import _is_installed


def test_cmd_plugins_list():
    """Plugins list shows available plugins with status."""
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_list(Namespace(), {})
    sys.stdout = old
    output = out.getvalue()
    assert "Plugins:" in output
    assert "javascript" in output
    assert "tiktoken" in output


def test_cmd_plugins_install_unknown():
    """Install unknown plugin returns error message."""
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_install(Namespace(language="unknown_lang", execute=False), {})
    sys.stdout = old
    assert "Unknown plugin" in out.getvalue()


def test_cmd_plugins_uninstall_unknown():
    """Uninstall unknown plugin returns error message."""
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_uninstall(Namespace(language="unknown_lang"), {})
    sys.stdout = old
    assert "Unknown plugin" in out.getvalue()


@pytest.mark.skipif(not _is_installed("tree_sitter"), reason="tree_sitter not installed")
def test_cmd_plugins_install_already_installed():
    """Install already-installed plugin shows status."""
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_install(Namespace(language="javascript", execute=False), {})
    sys.stdout = old
    output = out.getvalue()
    assert "already installed" in output


@pytest.mark.skipif(not _is_installed("tiktoken"), reason="tiktoken not installed")
def test_cmd_plugins_uninstall_installed():
    """Uninstall installed plugin shows pip command."""
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_uninstall(Namespace(language="tiktoken"), {})
    sys.stdout = old
    output = out.getvalue()
    assert "pip uninstall" in output


def test_dispatch_plugins_unknown_command():
    """Unknown plugins subcommand exits with error."""
    parser = ArgumentParser()
    plugins_sub = parser.add_subparsers(dest="command")
    plugins_sub.add_parser("plugins")

    config = {
        "project_name": "test",
        "output_dir": "out",
        "_root": ".",
        "profiles": {},
    }

    args = Namespace(plugins_command="unknown_cmd")

    with pytest.raises(SystemExit):
        _dispatch_plugins(args, config, parser)
