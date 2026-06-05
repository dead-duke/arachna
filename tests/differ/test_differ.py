"""Tests for LLM-optimized differ."""

from arachna.differ import DiffSection, compute_diff, compute_diff_stats


def test_modified_file_markdown():
    """Modified file produces REMOVED/ADDED blocks."""
    old_content = "line1\nline2\nline3\n"
    new_content = "line1\nline2 changed\nline3\n"
    result = compute_diff(old_content, new_content, "src/main.py")
    assert "### src/main.py" in result
    assert "REMOVED" in result
    assert "ADDED" in result
    assert "line2" in result
    assert "line2 changed" in result


def test_modified_file_xml():
    """Modified file produces XML diff."""
    old_content = "line1\nline2\nline3\n"
    new_content = "line1\nline2 changed\nline3\n"
    result = compute_diff(old_content, new_content, "src/main.py", fmt="xml")
    assert '<file path="src/main.py">' in result
    assert "<removed>" in result
    assert "<added>" in result


def test_added_file():
    """New file shows full content."""
    new_content = "print('hello')\nprint('world')\n"
    result = compute_diff("", new_content, "src/new.py")
    assert "ADDED (new file)" in result
    assert "print('hello')" in result


def test_added_file_xml():
    """New file in XML format."""
    new_content = "print('hello')\n"
    result = compute_diff("", new_content, "src/new.py", fmt="xml")
    assert '<file path="src/new.py">' in result
    assert "<added>" in result
    assert "print('hello')" in result


def test_deleted_file():
    """Deleted file shows [DELETED]."""
    result = compute_diff("old content", "", "src/old.py")
    assert "[DELETED]" in result


def test_deleted_file_xml():
    """Deleted file in XML format."""
    result = compute_diff("old content", "", "src/old.py", fmt="xml")
    assert '<file path="src/old.py">' in result
    assert "<removed>" in result
    assert "[DELETED]" in result


def test_unchanged_file():
    """Unchanged file returns empty string."""
    content = "same\ncontent\n"
    result = compute_diff(content, content, "src/same.py")
    assert result == ""


def test_empty_to_non_empty():
    """Empty old file → all lines added."""
    result = compute_diff("", "new content\n", "src/grew.py")
    assert "ADDED (new file)" in result


def test_non_empty_to_empty():
    """Non-empty old file → deleted."""
    result = compute_diff("old content\n", "", "src/gone.py")
    assert "[DELETED]" in result


def test_compute_diff_stats():
    """compute_diff_stats aggregates correctly with renamed and moved."""
    diffs = [
        DiffSection(type="modified", path="a.py", content="diff a"),
        DiffSection(type="modified", path="b.py", content="diff b"),
        DiffSection(type="added", path="c.py", content="new file"),
        DiffSection(type="deleted", path="d.py", content="[DELETED]"),
        DiffSection(
            type="renamed", path="e.py", old_path="old_e.py", similarity=0.95, content="diff e"
        ),
        DiffSection(type="moved", path="sub/f.py", old_path="f.py", similarity=1.0, content=""),
    ]
    stats = compute_diff_stats(diffs)
    assert stats["modified"] == 2
    assert stats["added"] == 1
    assert stats["deleted"] == 1
    assert stats["renamed"] == 1
    assert stats["moved"] == 1
    assert stats["tokens"] > 0


def test_compute_diff_stats_all_zero():
    """Empty diff list returns zeros."""
    stats = compute_diff_stats([])
    assert stats["modified"] == 0
    assert stats["added"] == 0
    assert stats["deleted"] == 0
    assert stats["renamed"] == 0
    assert stats["moved"] == 0
    assert stats["tokens"] == 0


def test_diff_section_similarity_field():
    """DiffSection accepts similarity and old_path fields."""
    section = DiffSection(
        type="renamed",
        path="src/new.py",
        old_path="src/old.py",
        similarity=0.87,
        content="diff here",
    )
    assert section.type == "renamed"
    assert section.path == "src/new.py"
    assert section.old_path == "src/old.py"
    assert section.similarity == 0.87


def test_diff_section_defaults():
    """DiffSection defaults are correct."""
    section = DiffSection(type="added", path="new.py", content="hello")
    assert section.old_path is None
    assert section.similarity is None


def test_binary_changed_markdown():
    """Binary files can still be diffed as text (no special handling in MVP)."""
    result = compute_diff("binary\x00data", "binary\x01data", "data.bin")
    # Should not crash — difflib handles any string
    assert "### data.bin" in result
