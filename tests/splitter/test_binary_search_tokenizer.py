"""Tests for binary search with custom tokenizers (v2.9.2)."""

from arachna.splitter import _handle_single


def test_binary_search_custom_tokenizer():
    """Custom tokenizer uses binary search for truncation."""
    call_count = [0]

    def counting_tok(text):
        call_count[0] += 1
        return len(text) // 4

    text = "x" * 1000
    parts, was_truncated = _handle_single(text, 100, tokenizer=counting_tok)
    assert was_truncated
    assert "truncated" in parts[0]
    assert call_count[0] > 0


def test_binary_search_max_iterations_guard():
    """Non-monotonic tokenizer doesn't loop forever."""
    call_count = [0]

    def non_monotonic(text):
        call_count[0] += 1
        return 500 if len(text) > 500 else 1

    text = "x" * 1000
    parts, was_truncated = _handle_single(text, 100, tokenizer=non_monotonic)
    assert was_truncated
    assert call_count[0] <= 110  # 100 max iterations + some


def test_default_tokenizer_fast_path():
    """Default tokenizer uses O(1) fast path."""
    text = "x" * 1000
    parts, was_truncated = _handle_single(text, 100)
    assert was_truncated
    assert "truncated" in parts[0]
    # Fast path: 4 chars ≈ 1 token → limit = 100 * 4 = 400 chars
    assert len(parts[0]) <= 500
