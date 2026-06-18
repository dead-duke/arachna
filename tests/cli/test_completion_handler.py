"""Tests for cli/completion.py handler — bash, zsh, and edge cases."""

import sys
from argparse import Namespace
from io import StringIO

from arachna.cli.completion import _cmd_completion


def test_cmd_completion_bash():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_completion(Namespace(shell="bash"), {})
    sys.stdout = old
    assert "complete -F _arachna_complete arachna" in out.getvalue()


def test_cmd_completion_zsh():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_completion(Namespace(shell="zsh"), {})
    sys.stdout = old
    assert "#compdef arachna" in out.getvalue()


def test_cmd_completion_unknown_shell():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_completion(Namespace(shell="fish"), {})
    sys.stdout = old
    assert "Usage:" in out.getvalue()
    assert "source <(arachna completion bash)" in out.getvalue()
