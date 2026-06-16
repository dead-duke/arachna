"""Tests for oversized section splitting in split_sections."""

from arachna.domain.splitter import _split_oversized_section, split_sections
from arachna.domain.tokenizer import count_tokens


def test_split_oversized_by_paragraphs():
    """Section with paragraph breaks splits cleanly."""
    section = "para1\n\npara2\n\npara3\n\npara4"
    chunks = _split_oversized_section(section, max_tokens=2, tokenizer=count_tokens)
    assert len(chunks) > 1
    for chunk in chunks:
        assert count_tokens(chunk) <= 3


def test_split_oversized_by_lines():
    """Paragraph-free section splits by lines."""
    section = "line1\nline2\nline3\nline4"
    chunks = _split_oversized_section(section, max_tokens=2, tokenizer=count_tokens)
    assert len(chunks) > 1
    for chunk in chunks:
        assert count_tokens(chunk) <= 2


def test_split_oversized_minified_code():
    """Single line > max_tokens falls back to character split."""
    section = "x" * 2000
    chunks = _split_oversized_section(section, max_tokens=100, tokenizer=count_tokens)
    assert len(chunks) > 1
    for chunk in chunks:
        assert count_tokens(chunk) <= 100


def test_split_oversized_exact_boundary():
    """Section exactly at max_tokens returns single chunk."""
    section = "hello world"
    tokens = count_tokens(section)
    chunks = _split_oversized_section(section, max_tokens=tokens, tokenizer=count_tokens)
    assert len(chunks) == 1
    assert chunks[0] == section


def test_split_oversized_no_content_loss():
    """All content preserved after splitting (markers removed)."""
    section = "line1\nline2\nline3\nline4"
    chunks = _split_oversized_section(section, max_tokens=2, tokenizer=count_tokens)
    reconstructed = "\n".join(chunks)
    assert section in reconstructed


def test_split_sections_oversized_markers():
    """Continuation markers present and correctly positioned."""
    sections = ["x" * 2000]
    parts, indices = split_sections(sections, max_tokens=100, tokenizer=count_tokens)
    assert len(parts) > 1
    assert "CONTINUES in part" in parts[0]
    assert "CONTINUED from part" in parts[-1]
    if len(parts) > 2:
        assert "CONTINUED from part" in parts[1]
        assert "CONTINUES in part" in parts[1]


def test_split_sections_oversized_indices():
    """All chunks share same original section index."""
    sections = ["x" * 2000]
    parts, indices = split_sections(sections, max_tokens=100, tokenizer=count_tokens)
    for idx_list in indices:
        assert idx_list == [0]


def test_split_sections_mixed():
    """Mix of normal and oversized sections packs correctly."""
    sections = ["short1", "short2", "x" * 2000, "short3"]
    parts, indices = split_sections(sections, max_tokens=100, tokenizer=count_tokens)
    assert len(parts) >= 4
    oversized_parts = [idx_list for idx_list in indices if idx_list == [2]]
    assert len(oversized_parts) > 1


def test_split_sections_base64():
    """Long base64 string splits at safe boundaries."""
    section = "ABCD" * 500
    parts, indices = split_sections([section], max_tokens=100, tokenizer=count_tokens)
    assert len(parts) > 1
    for part in parts:
        assert count_tokens(part) <= 120


def test_split_sections_toc_dedup():
    """TOC _build_toc deduplicates indices within a part."""
    from arachna.domain.collector import _build_toc

    sections = [("src/big.py", "x" * 2000, 500)]
    parts, indices = split_sections([sections[0][1]], max_tokens=100, tokenizer=count_tokens)
    toc = _build_toc(sections, indices[0], 1, len(parts), all_indices=indices)
    assert "big.py" in toc
    assert "split across" in toc
    assert toc.count("big.py") == 1
