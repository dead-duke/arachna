"""Tests for plugins CLI — empty state."""

import sys
from argparse import Namespace
from io import StringIO
from unittest.mock import patch

from arachna.cli.plugins import _cmd_plugins_list


def test_plugins_list_empty():
    """No plugins available shows message."""
    with patch("arachna.cli.plugins.list_plugins", return_value={}):
        out = StringIO()
        old = sys.stdout
        sys.stdout = out
        _cmd_plugins_list(Namespace(), {})
        sys.stdout = old
        assert "No plugins available" in out.getvalue()
