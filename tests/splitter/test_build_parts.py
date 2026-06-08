from unittest.mock import MagicMock

from hypothesis import given
from hypothesis import strategies as st

from arachna.splitter import _build_parts, split_sections


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
    mock_tok = MagicMock(return_value=1)
    _build_parts(["a", "b", "c"], max_tokens=100, tokenizer=mock_tok)
    assert mock_tok.called


def test_custom_tokenizer_small_limit():
    call_count = [0]

    def counting_tok(text):
        call_count[0] += 1
        return 2

    parts = _build_parts(["aa", "bb", "cc"], max_tokens=3, tokenizer=counting_tok)
    assert len(parts) == 3
    assert call_count[0] > 0


# ── Property-based tests ──────────────────────────────────────────


@given(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=20))
def test_split_sections_preserves_content(sections):
    """All section content appears in at least one part."""
    parts = split_sections(sections, max_tokens=10000)
    all_text = "".join(parts)
    for section in sections:
        if section.strip():
            assert section.strip() in all_text


@given(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=20))
def test_split_sections_no_empty_parts(sections):
    """No part is empty."""
    parts = split_sections(sections, max_tokens=10000)
    for part in parts:
        assert part.strip() != ""


@given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=10))
def test_split_sections_count_at_least_one_if_any_non_empty(sections):
    """If any section has non-whitespace content, at least one part produced."""
    parts = split_sections(sections, max_tokens=10000)
    has_content = any(s.strip() for s in sections)
    if has_content:
        assert len(parts) >= 1


@given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=10))
def test_split_sections_small_limit_many_parts(sections):
    """With very small max_tokens, each section becomes its own part."""
    parts = split_sections(sections, max_tokens=1)
    non_empty = [s for s in sections if s.strip()]
    if non_empty:
        assert len(parts) >= len(non_empty)
