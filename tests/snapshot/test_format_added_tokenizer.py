"""Tests for _format_added with tokenizer parameter."""

from arachna.snapshot.diff.differ import compute_diff


def test_format_added_with_custom_tokenizer():
    """_format_added uses custom tokenizer for accurate truncation."""
    new_content = "x" * 2000

    def custom_tok(text):
        return len(text) // 2

    result = compute_diff("", new_content, "src/big.py", max_tokens=100, tokenizer=custom_tok)
    assert "truncated" in result
    assert "src/big.py" in result


def test_format_added_default_tokenizer():
    """_format_added works with default tokenizer (not specified)."""
    new_content = "x" * 2000
    result = compute_diff("", new_content, "src/big.py", max_tokens=100)
    assert "truncated" in result


def test_format_added_within_limit_no_truncation():
    """_format_added does not truncate when content fits."""
    new_content = "short file"
    result = compute_diff("", new_content, "src/small.py", max_tokens=1000)
    assert "truncated" not in result
    assert "short file" in result
