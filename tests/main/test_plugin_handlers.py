"""Tests for plugin handlers in __main__.py — with real plugins installed."""

from argparse import Namespace

from arachna.__main__ import (
    _cmd_plugins_install,
    _cmd_plugins_list,
    _cmd_plugins_uninstall,
)


def test_cmd_plugins_list_with_real_plugins():
    """_cmd_plugins_list shows installed plugins (tree-sitter, tiktoken are installed)."""
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_list(Namespace(), {})
    sys.stdout = old
    output = out.getvalue()
    assert "Plugins:" in output
    assert "javascript" in output
    assert "tiktoken" in output


def test_cmd_plugins_install_already_installed():
    """_cmd_plugins_install for already installed plugin shows 'already installed'."""
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_install(Namespace(language="javascript", execute=False), {})
    sys.stdout = old
    output = out.getvalue()
    assert "already installed" in output


def test_cmd_plugins_uninstall_installed():
    """_cmd_plugins_uninstall for installed plugin shows pip uninstall command."""
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_uninstall(Namespace(language="tiktoken"), {})
    sys.stdout = old
    output = out.getvalue()
    assert "pip uninstall" in output
