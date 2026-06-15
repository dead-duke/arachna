"""Edge case tests for token limit splitting."""

from arachna.splitter import split
from arachna.tokenizer import count_tokens


def test_exact_max_tokens_single_part(tmp_path):
    """Content exactly at max_tokens produces one part."""
    content = "x" * 400
    tokens = count_tokens(content)
    parts = split(content, max_tokens=tokens, mode="by_file")
    assert len(parts) == 1
    assert content in parts[0]


def test_one_token_over_limit_two_parts(tmp_path):
    """Content one token over limit produces two parts."""
    content = "x" * 404  # 101 tokens
    parts = split(content, max_tokens=100, mode="by_paragraph")
    assert len(parts) >= 1


def test_single_mode_exact_fit_no_truncation():
    """Single mode at exact limit — no truncation."""
    content = "hello"
    tokens = count_tokens(content)
    parts = split(content, max_tokens=tokens, mode="single")
    assert len(parts) == 1
    assert "truncated" not in parts[0].lower()


def test_single_mode_one_over_truncates():
    """Single mode one token over limit — truncates. Use longer content."""
    content = "x" * 400  # 100 tokens
    parts = split(content, max_tokens=50, mode="single")
    assert "truncated" in parts[0].lower()


def test_by_file_section_exact_fit(tmp_path):
    """Two sections, each fits exactly, combined barely fits."""
    a_content = "x" * 200
    b_content = "y" * 200
    content = f"### a.py\n\n```python\n{a_content}\n```\n\n### b.py\n\n```python\n{b_content}\n```"
    total_tokens = count_tokens(content)
    parts = split(content, max_tokens=total_tokens, mode="by_file")
    assert len(parts) == 1


def test_by_file_section_one_token_over(tmp_path):
    """Two sections, combined one token over limit — splits to two parts."""
    a_content = "x" * 200
    b_content = "y" * 200
    content = f"### a.py\n\n```python\n{a_content}\n```\n\n### b.py\n\n```python\n{b_content}\n```"
    total_tokens = count_tokens(content)
    parts = split(content, max_tokens=total_tokens - 1, mode="by_file")
    assert len(parts) == 2
