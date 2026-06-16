"""Edge case test for completion handler — unknown shell."""

import sys
from argparse import Namespace
from io import StringIO

from arachna.cli.completion import _cmd_completion


def test_cmd_completion_unknown_shell():
    """_cmd_completion with unknown shell prints usage."""
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_completion(Namespace(shell="fish"), {})
    sys.stdout = old
    assert "Usage:" in out.getvalue()
    assert "source <(arachna completion bash)" in out.getvalue()
