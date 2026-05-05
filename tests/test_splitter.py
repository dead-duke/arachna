"""Tests for splitter — split modes and boundary conditions."""

from arachna.splitter import _build_parts, _split_to_sections, split


# _split_to_sections
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


def test_split_to_sections_marker_at_start():
    sections = _split_to_sections("\n\n### first\n\n### second", "\n\n### ")
    assert len(sections) == 2
    assert sections[0] == "\n\n### first"
    assert sections[1] == "\n\n### second"


# _build_parts
def test_build_parts_single_section():
    parts = _build_parts(["hello world"], max_tokens=100)
    assert len(parts) == 1
    assert parts[0] == "hello world"


def test_build_parts_multiple_fit():
    parts = _build_parts(["a", "b", "c"], max_tokens=100)
    assert len(parts) == 1


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


def test_build_parts_mixed_sizes():
    """Small and large sections mixed."""
    sections = ["small", "x" * 500, "medium", "y" * 500]
    parts = _build_parts(sections, max_tokens=10)
    assert len(parts) == 4


# split() integration
def test_split_by_file():
    content = (
        "### a.py\n\n```python\nprint('hello')\n```\n\n### b.py\n\n```python\nprint('world')\n```\n"
    )
    parts = split(content, max_tokens=10000, mode="by_file")
    assert len(parts) == 1


def test_split_by_file_multiple_parts():
    content = (
        "### a.py\n\n```python\n"
        + "x" * 500
        + "\n```\n\n### b.py\n\n```python\n"
        + "y" * 500
        + "\n```\n"
    )
    parts = split(content, max_tokens=10, mode="by_file")
    assert len(parts) > 1


def test_split_by_paragraph():
    content = "para1\n\npara2\n\npara3"
    parts = split(content, max_tokens=10000, mode="by_paragraph")
    assert len(parts) == 1


def test_split_by_paragraph_small_limit():
    content = "a" * 200 + "\n\n" + "b" * 200
    parts = split(content, max_tokens=10, mode="by_paragraph")
    assert len(parts) == 2


def test_split_by_marker():
    content = "=== A ===\nhello\n\n=== B ===\nworld"
    parts = split(content, max_tokens=10000, mode="by_marker", marker="\n\n=== ")
    assert len(parts) == 1


def test_split_by_marker_multiple():
    content = "\n\n=== A ===\n" + "x" * 500 + "\n\n=== B ===\n" + "y" * 500
    parts = split(content, max_tokens=10, mode="by_marker", marker="\n\n=== ")
    assert len(parts) == 2


def test_split_single_mode():
    content = "hello world"
    parts = split(content, max_tokens=10000, mode="single")
    assert len(parts) == 1
    assert parts[0] == "hello world"


def test_split_single_truncation():
    content = "x" * 500
    parts = split(content, max_tokens=10, mode="single")
    assert len(parts) == 1
    assert "truncated" in parts[0].lower()


def test_split_unknown_mode_falls_back():
    content = "hello world"
    parts = split(content, max_tokens=10000, mode="unknown_mode")
    assert len(parts) == 1
    assert parts[0] == "hello world"


def test_split_empty_content():
    parts = split("", max_tokens=100, mode="by_file")
    assert len(parts) == 0


def test_split_content_fits_exactly():
    content = "aaaa"
    parts = split(content, max_tokens=1, mode="by_paragraph")
    assert len(parts) == 1


def test_split_single_empty():
    parts = split("", max_tokens=100, mode="single")
    assert len(parts) == 1
    assert parts[0] == ""
