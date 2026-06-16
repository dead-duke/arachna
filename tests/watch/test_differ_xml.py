"""Tests for XML format branches in differ.py."""

from arachna.watch.differ import compute_diff


def test_added_file_xml():
    """New file in XML format."""
    new_content = "print('hello')\n"
    result = compute_diff("", new_content, "src/new.py", fmt="xml")
    assert '<file path="src/new.py">' in result
    assert "<added>" in result
    assert "print('hello')" in result


def test_deleted_file_xml():
    """Deleted file in XML format."""
    result = compute_diff("old content", "", "src/old.py", fmt="xml")
    assert '<file path="src/old.py">' in result
    assert "<removed>" in result
    assert "[DELETED]" in result


def test_modified_xml_multiline():
    """Modified file with multiple changed blocks in XML."""
    old_content = "line1\nline2\nline3\nline4\nline5\n"
    new_content = "line1\nCHANGED2\nline3\nCHANGED4\nline5\n"
    result = compute_diff(old_content, new_content, "src/multi.py", fmt="xml")
    assert '<file path="src/multi.py">' in result
    assert "<removed>" in result
    assert "<added>" in result


def test_modified_xml_single_block():
    """Modified file with one changed block in XML."""
    old_content = "before\nold middle\nafter\n"
    new_content = "before\nnew middle\nafter\n"
    result = compute_diff(old_content, new_content, "src/single.py", fmt="xml")
    assert '<file path="src/single.py">' in result
    assert "<removed>" in result
    assert "<added>" in result
