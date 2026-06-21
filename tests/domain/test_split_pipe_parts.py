"""Tests for _split_pipe_parts edge cases in runner.py."""

from arachna.domain.execution.runner import _split_pipe_parts


def test_escaped_pipe_treated_as_literal():
    r"""\| is treated as literal |, not a pipe separator."""
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

    In shell: echo \| grep -> the \ escapes |, making it literal.
    In _split_pipe_parts: ch='\\', next_ch='|' -> escaped pipe, append '|' as literal.
    """
    parts = _split_pipe_parts(r"echo \| grep")
    assert len(parts) == 1
    assert "|" in parts[0]
    assert "grep" in parts[0]


def test_double_backslash_before_pipe():
    r"""\\| — backslash is escaped, pipe is literal.

    In _split_pipe_parts: ch='\\', next_ch='\\' -> escaped backslash, append one '\\'.
    Then ch='|' without preceding backslash -> pipe separator.
    Result: split into two parts, first part contains single literal backslash.
    """
    parts = _split_pipe_parts("echo \\\\| grep")
    assert len(parts) == 2, f"Expected 2 parts, got {len(parts)}: {parts}"
    assert "grep" in parts[1]


def test_escaped_backslash_escaped_pipe():
    r"""\\\| — backslash escaped, then escaped pipe.

    In _split_pipe_parts: ch='\\', next_ch='\\' -> escaped backslash, append '\\'.
    Then ch='\\', next_ch='|' -> escaped pipe, append '|' as literal.
    Result: no split, pipe is literal.
    """
    parts = _split_pipe_parts("echo \\\\\\| grep")
    assert len(parts) == 1, f"Expected 1 part, got {len(parts)}: {parts}"
    assert "|" in parts[0]
    assert "grep" in parts[0]


def test_backslash_at_end_of_string():
    r"""Trailing backslash — no next character to check."""
    parts = _split_pipe_parts("echo hello\\")
    assert len(parts) == 1
    assert "hello\\" in parts[0]


def test_empty_command():
    """Empty string returns single empty part."""
    parts = _split_pipe_parts("")
    assert parts == [""]


def test_simple_no_pipe():
    """Command without any pipe returns single part."""
    parts = _split_pipe_parts("echo hello world")
    assert len(parts) == 1
    assert parts[0] == "echo hello world"


def test_escaped_double_quote_inside_double_quotes():
    r"""Escaped double quote inside double quotes — pipe still not a separator."""
    parts = _split_pipe_parts(r'echo "hello \"world|test\""')
    assert len(parts) == 1, f"Expected 1 part, got {len(parts)}: {parts}"


def test_backslash_escape_dollar_in_double_quotes():
    r"""Backslash before $ inside double quotes — $ is literal, still inside quotes."""
    parts = _split_pipe_parts(r'echo "\$HOME"')
    assert len(parts) == 1
    assert "$HOME" in parts[0]


def test_single_quote_inside_double_quotes():
    """Single quote inside double quotes — not a quote boundary."""
    parts = _split_pipe_parts('echo "it\'s a pipe|test"')
    assert len(parts) == 1, f"Expected 1 part, got {len(parts)}: {parts}"


def test_multiple_escaped_backslashes():
    r"""Chain of four backslashes: \\\\| -> \\ is literal \\, | is pipe."""
    parts = _split_pipe_parts("echo \\\\\\\\| grep")
    assert len(parts) == 2, f"Expected 2 parts, got {len(parts)}: {parts}"
    assert "grep" in parts[1]
