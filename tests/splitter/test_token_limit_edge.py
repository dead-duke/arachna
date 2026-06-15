"""Edge case tests for token limit splitting."""

from arachna.domain.splitter import split
from arachna.domain.tokenizer import count_tokens


def test_exact_max_tokens_single_part(tmp_path):
    content = "x" * 400
    tokens = count_tokens(content)
    parts = split(content, max_tokens=tokens, mode="by_file")
    assert len(parts) == 1
    assert content in parts[0]


def test_one_token_over_limit_two_parts(tmp_path):
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


def test_by_file_section_exact_fit(tmp_path):
    a_content = "x" * 200
    b_content = "y" * 200
    content = f"### a.py\n\n```python\n{a_content}\n```\n\n### b.py\n\n```python\n{b_content}\n```"
    total_tokens = count_tokens(content)
    parts = split(content, max_tokens=total_tokens, mode="by_file")
    assert len(parts) == 1


def test_by_file_section_one_token_over(tmp_path):
    a_content = "x" * 200
    b_content = "y" * 200
    content = f"### a.py\n\n```python\n{a_content}\n```\n\n### b.py\n\n```python\n{b_content}\n```"
    total_tokens = count_tokens(content)
    parts = split(content, max_tokens=total_tokens - 1, mode="by_file")
    assert len(parts) == 2
