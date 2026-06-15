import sys
from io import StringIO
from unittest.mock import patch

from arachna.config.completion import generate_bash, generate_zsh, main


def test_generate_bash_contains_arachna():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    generate_bash()
    sys.stdout = old
    result = out.getvalue()
    assert "complete -F _arachna_complete arachna" in result
    assert "--profile" in result
    assert "--all" in result
    assert "--format" in result


def test_generate_zsh_contains_arachna():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    generate_zsh()
    sys.stdout = old
    result = out.getvalue()
    assert "#compdef arachna" in result
    assert "--profile" in result
    assert "--all" in result


def test_generate_bash_syntax():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    generate_bash()
    sys.stdout = old
    result = out.getvalue()
    assert result.startswith("_arachna_complete()")
    assert "COMPREPLY" in result


def test_generate_zsh_syntax():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    generate_zsh()
    sys.stdout = old
    result = out.getvalue()
    assert result.startswith("#compdef arachna")
    assert "_arguments" in result


def test_main_bash():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    with patch("sys.argv", ["completion", "bash"]):
        main()
    sys.stdout = old
    assert "complete -F _arachna_complete arachna" in out.getvalue()


def test_main_zsh():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    with patch("sys.argv", ["completion", "zsh"]):
        main()
    sys.stdout = old
    assert "#compdef arachna" in out.getvalue()


def test_main_no_args():
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    with patch("sys.argv", ["completion"]):
        main()
    sys.stdout = old
    result = out.getvalue()
    assert "source <(arachna completion bash)" in result
    assert "source <(arachna completion zsh)" in result
