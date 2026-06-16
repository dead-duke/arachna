"""Tests for unlimited mode in splitter.py."""

from arachna.domain.splitter import pack_into_parts, split, split_sections
from arachna.domain.tokenizer import count_tokens


def test_pack_into_parts_unlimited():
    sections = ["section1", "section2", "section3"]
    parts, indices = pack_into_parts(sections, -1, tokenizer=count_tokens)
    assert len(parts) == 1
    assert len(indices) == 1
    assert indices[0] == [0, 1, 2]
    assert "section1" in parts[0]
    assert "section2" in parts[0]
    assert "section3" in parts[0]


def test_split_unlimited():
    content = "### a.py\n\n```python\ncode\n```\n\n### b.py\n\n```python\ncode\n```"
    parts = split(content, -1, mode="by_file")
    assert len(parts) == 1


def test_split_sections_unlimited():
    sections = ["a", "b", "c"]
    parts, indices = split_sections(sections, -1, tokenizer=count_tokens)
    assert len(parts) == 1
    assert indices[0] == [0, 1, 2]


def test_split_unlimited_by_paragraph():
    parts = split("para1\n\npara2\n\npara3", -1, mode="by_paragraph")
    assert len(parts) == 1


def test_split_unlimited_single():
    parts = split("hello world", -1, mode="single")
    assert len(parts) == 1
    assert "hello world" in parts[0]
