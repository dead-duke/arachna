"""Tests for cli/plugins.py handlers."""

import sys
from argparse import Namespace
from io import StringIO

from arachna.cli.plugins import _cmd_plugins_install, _cmd_plugins_list, _cmd_plugins_uninstall


def test_cmd_plugins_list_real():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_list(Namespace(), {})
    sys.stdout = old
    output = out.getvalue()
    assert "Plugins:" in output
    assert "javascript" in output


def test_cmd_plugins_install_unknown():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_install(Namespace(language="unknown_lang", execute=False), {})
    sys.stdout = old
    assert "Unknown plugin" in out.getvalue()


def test_cmd_plugins_uninstall_unknown():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_uninstall(Namespace(language="unknown_lang"), {})
    sys.stdout = old
    assert "Unknown plugin" in out.getvalue()
