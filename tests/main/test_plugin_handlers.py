"""Tests for plugin handlers in __main__.py — with real plugins installed."""

from argparse import Namespace

import pytest

from arachna.cli.plugins import (
    _cmd_plugins_install,
    _cmd_plugins_list,
    _cmd_plugins_uninstall,
)
from arachna.plugins.plugins import _is_installed


def test_cmd_plugins_list_with_real_plugins():
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


@pytest.mark.skipif(not _is_installed("tree_sitter"), reason="tree_sitter not installed")
def test_cmd_plugins_install_already_installed():
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_install(Namespace(language="javascript", execute=False), {})
    sys.stdout = old
    output = out.getvalue()
    assert "already installed" in output


@pytest.mark.skipif(not _is_installed("tiktoken"), reason="tiktoken not installed")
def test_cmd_plugins_uninstall_installed():
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_uninstall(Namespace(language="tiktoken"), {})
    sys.stdout = old
    output = out.getvalue()
    assert "pip uninstall" in output
