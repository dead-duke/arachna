import sys
from io import StringIO

from arachna.config.completion import generate_bash, generate_zsh


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
