"""Tests for splitter — token-limited part building."""

from arachna.splitter import _build_parts, _split_to_sections


def test_build_parts_single_section():
    parts = _build_parts(["hello world"], max_tokens=100)
    assert len(parts) == 1
    assert parts[0] == "hello world"


def test_build_parts_multiple_fit():
    parts = _build_parts(["a", "b", "c"], max_tokens=100)
    assert len(parts) == 1
    assert "a" in parts[0] and "b" in parts[0] and "c" in parts[0]


def test_build_parts_exceed_limit():
    sections = ["a" * 40, "b" * 40, "c" * 40]
    parts = _build_parts(sections, max_tokens=2)
    assert len(parts) == 3


def test_build_parts_single_exceeds_limit():
    parts = _build_parts(["a" * 100], max_tokens=1)
    assert len(parts) == 1


def test_build_parts_exact_fit():
    parts = _build_parts(["aaaa", "bbbb"], max_tokens=2)
    assert len(parts) == 1


def test_build_parts_empty_sections():
    parts = _build_parts(["", "  ", "\n"], max_tokens=100)
    assert len(parts) == 0


def test_split_to_sections_restores_marker():
    sections = _split_to_sections("one\n\n### two\n\n### three", "\n\n### ")
    assert len(sections) == 3
    assert sections[0] == "one"
    assert sections[1] == "\n\n### two"
    assert sections[2] == "\n\n### three"


def test_split_to_sections_no_marker():
    sections = _split_to_sections("hello world", "\n\n### ")
    assert len(sections) == 1
    assert sections[0] == "hello world"


def test_split_to_sections_empty():
    sections = _split_to_sections("", "\n\n### ")
    assert len(sections) == 0
