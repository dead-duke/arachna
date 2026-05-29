from unittest.mock import MagicMock

from arachna.splitter import split


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
    """Custom tokenizer is called when passed to split in by_file mode."""
    mock_tok = MagicMock(return_value=1)
    content = "### a.py\n\n```python\nprint('hello')\n```"
    split(content, max_tokens=10000, mode="by_file", tokenizer=mock_tok)
    assert mock_tok.called


def test_custom_tokenizer_single():
    """Custom tokenizer is called when passed to split in single mode."""
    mock_tok = MagicMock(return_value=5)
    split("hello world", max_tokens=10000, mode="single", tokenizer=mock_tok)
    assert mock_tok.called


def test_custom_tokenizer_by_paragraph():
    """Custom tokenizer is called when passed to split in by_paragraph mode."""
    mock_tok = MagicMock(return_value=1)
    split("para1\n\npara2", max_tokens=10000, mode="by_paragraph", tokenizer=mock_tok)
    assert mock_tok.called
