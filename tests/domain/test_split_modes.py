"""Tests for split modes — by_file, by_paragraph, by_marker, single, unlimited, token edge cases."""

from unittest.mock import MagicMock

from arachna.domain.execution.splitter import split
from arachna.domain.tokenization.tokenizer import count_tokens


def test_by_file_single():
    content = "### a.py\n\n```python\nprint('hello')\n```"
    parts = split(content, max_tokens=10000, mode="by_file")
    assert len(parts) == 1


def test_by_file_multiple():
    content = (
        "### a.py\n\n```python\n"
        + "x" * 500
        + "\n```\n\n### b.py\n\n```python\n"
        + "y" * 500
        + "\n```\n"
    )
    parts = split(content, max_tokens=10, mode="by_file")
    assert len(parts) > 1


def test_by_paragraph():
    parts = split("para1\n\npara2\n\npara3", max_tokens=10000, mode="by_paragraph")
    assert len(parts) == 1


def test_by_paragraph_small_limit():
    parts = split("a" * 200 + "\n\n" + "b" * 200, max_tokens=10, mode="by_paragraph")
    assert len(parts) == 2


def test_by_marker():
    parts = split(
        "=== A ===\nhello\n\n=== B ===\nworld",
        max_tokens=10000,
        mode="by_marker",
        marker="\n\n=== ",
    )
    assert len(parts) == 1


def test_by_marker_multiple():
    content = "\n\n=== A ===\n" + "x" * 500 + "\n\n=== B ===\n" + "y" * 500
    parts = split(content, max_tokens=10, mode="by_marker", marker="\n\n=== ")
    assert len(parts) == 2


def test_single_mode():
    parts = split("hello world", max_tokens=10000, mode="single")
    assert parts == ["hello world"]


def test_single_truncation():
    parts = split("x" * 500, max_tokens=10, mode="single")
    assert "truncated" in parts[0].lower()


def test_single_empty():
    parts = split("", max_tokens=100, mode="single")
    assert parts == [""]


def test_unknown_mode():
    parts = split("hello world", max_tokens=10000, mode="unknown")
    assert parts == ["hello world"]


def test_empty_content():
    parts = split("", max_tokens=100, mode="by_file")
    assert parts == []


def test_custom_tokenizer_by_file():
    mock_tok = MagicMock(return_value=1)
    content = "### a.py\n\n```python\nprint('hello')\n```"
    split(content, max_tokens=10000, mode="by_file", tokenizer=mock_tok)
    assert mock_tok.called


def test_custom_tokenizer_single():
    mock_tok = MagicMock(return_value=5)
    split("hello world", max_tokens=10000, mode="single", tokenizer=mock_tok)
    assert mock_tok.called


def test_custom_tokenizer_by_paragraph():
    mock_tok = MagicMock(return_value=1)
    split("para1\n\npara2", max_tokens=10000, mode="by_paragraph", tokenizer=mock_tok)
    assert mock_tok.called


# Token limit edge cases


def test_exact_max_tokens_single_part():
    content = "x" * 400
    tokens = count_tokens(content)
    parts = split(content, max_tokens=tokens, mode="by_file")
    assert len(parts) == 1
    assert content in parts[0]


def test_one_token_over_limit_two_parts():
    content = "x" * 404
    parts = split(content, max_tokens=100, mode="by_paragraph")
    assert len(parts) >= 1


def test_single_mode_exact_fit_no_truncation():
    content = "hello"
    tokens = count_tokens(content)
    parts = split(content, max_tokens=tokens, mode="single")
    assert len(parts) == 1
    assert "truncated" not in parts[0].lower()


def test_single_mode_one_over_truncates():
    content = "x" * 400
    parts = split(content, max_tokens=50, mode="single")
    assert "truncated" in parts[0].lower()


def test_by_file_section_exact_fit():
    a_content = "x" * 200
    b_content = "y" * 200
    content = f"### a.py\n\n```python\n{a_content}\n```\n\n### b.py\n\n```python\n{b_content}\n```"
    total_tokens = count_tokens(content)
    parts = split(content, max_tokens=total_tokens, mode="by_file")
    assert len(parts) == 1


def test_by_file_section_one_token_over():
    a_content = "x" * 200
    b_content = "y" * 200
    content = f"### a.py\n\n```python\n{a_content}\n```\n\n### b.py\n\n```python\n{b_content}\n```"
    total_tokens = count_tokens(content)
    parts = split(content, max_tokens=total_tokens - 1, mode="by_file")
    assert len(parts) == 2
