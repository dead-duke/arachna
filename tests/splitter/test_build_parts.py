from unittest.mock import MagicMock

from arachna.splitter import _build_parts


def test_single_section():
    parts = _build_parts(["hello world"], max_tokens=100)
    assert parts == ["hello world"]


def test_multiple_fit():
    parts = _build_parts(["a", "b", "c"], max_tokens=100)
    assert len(parts) == 1


def test_exceed_limit():
    parts = _build_parts(["a" * 40, "b" * 40, "c" * 40], max_tokens=2)
    assert len(parts) == 3


def test_single_exceeds():
    parts = _build_parts(["a" * 100], max_tokens=1)
    assert len(parts) == 1


def test_exact_fit():
    parts = _build_parts(["aaaa", "bbbb"], max_tokens=2)
    assert len(parts) == 1


def test_empty_sections():
    parts = _build_parts(["", "  ", "\n"], max_tokens=100)
    assert len(parts) == 0


def test_mixed_sizes():
    parts = _build_parts(["small", "x" * 500, "medium", "y" * 500], max_tokens=10)
    assert len(parts) == 4


def test_custom_tokenizer_called():
    """Custom tokenizer is used instead of default count_tokens."""
    mock_tok = MagicMock(return_value=1)
    _build_parts(["a", "b", "c"], max_tokens=100, tokenizer=mock_tok)
    assert mock_tok.called


def test_custom_tokenizer_small_limit():
    """Custom tokenizer with small limit produces multiple parts."""
    # Each section = 2 tokens. max_tokens=3 → aa(2) + bb(2)=4 > 3
    # → part1=[aa], part2=[bb], part3=[cc] = 3 parts
    call_count = [0]

    def counting_tok(text):
        call_count[0] += 1
        return 2

    parts = _build_parts(["aa", "bb", "cc"], max_tokens=3, tokenizer=counting_tok)
    assert len(parts) == 3
    assert call_count[0] > 0
