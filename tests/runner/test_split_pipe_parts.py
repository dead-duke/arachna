"""Tests for _split_pipe_parts edge cases in runner.py."""

from arachna.runner import _split_pipe_parts


def test_escaped_pipe_treated_as_literal():
    """\\| is treated as literal |, not a pipe separator."""
    parts = _split_pipe_parts(r"echo hello \| world")
    assert len(parts) == 1
    assert "hello | world" in parts[0]


def test_double_or_not_split():
    """|| is shell OR, not a pipe."""
    parts = _split_pipe_parts("cat file || echo fail")
    assert len(parts) == 1
    assert "||" in parts[0]


def test_pipe_inside_single_quotes_not_split():
    """| inside single quotes is not a separator."""
    parts = _split_pipe_parts("grep 'error|warning' file.txt")
    assert len(parts) == 1


def test_pipe_inside_double_quotes_not_split():
    """| inside double quotes is not a separator."""
    parts = _split_pipe_parts('grep "error|warning" file.txt')
    assert len(parts) == 1


def test_real_pipe_split():
    """Real pipe outside quotes splits correctly."""
    parts = _split_pipe_parts("cat file.txt | grep pattern | sort")
    assert len(parts) == 3
    assert parts[0] == "cat file.txt"
    assert parts[1] == "grep pattern"
    assert parts[2] == "sort"


def test_backslash_before_pipe():
    r"""\ before | outside quotes — \ is escape, | is literal.

    In shell: echo \| grep → the \ escapes |, making it literal.
    In _split_pipe_parts: ch='\\', next_ch='|' → escaped pipe, append '|' as literal.
    """
    parts = _split_pipe_parts(r"echo \| grep")
    assert len(parts) == 1
    assert "|" in parts[0]
    assert "grep" in parts[0]


def test_empty_command():
    """Empty string returns single empty part."""
    parts = _split_pipe_parts("")
    assert parts == [""]


def test_simple_no_pipe():
    """Command without any pipe returns single part."""
    parts = _split_pipe_parts("echo hello world")
    assert len(parts) == 1
    assert parts[0] == "echo hello world"
