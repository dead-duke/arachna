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


def test_dispatch_plugins_unknown_command_exits(tmp_path):
    """Unknown plugins command exits with error."""
    parser = ArgumentParser()
    plugins_sub = parser.add_subparsers(dest="command")
    plugins_sub.add_parser("plugins")

    config = {
        "project_name": "test",
        "output_dir": str(tmp_path / "out"),
        "_root": str(tmp_path),
        "profiles": {},
    }

    args = Namespace(plugins_command="unknown_cmd")

    with pytest.raises(SystemExit):
        _dispatch_plugins(args, config, parser)
