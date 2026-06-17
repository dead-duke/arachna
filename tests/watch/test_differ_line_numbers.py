"""Tests for line_numbers feature in differ.py — v4.2.0."""

from arachna.watch.differ import _format_added, _format_line_range, compute_diff


def test_format_line_range_with_line_numbers():
    lines = ["line1\n", "line2\n", "line3\n"]
    result = _format_line_range(1, 3, lines, line_numbers=True)
    assert "    2| line2" in result
    assert "    3| line3" in result


def test_format_line_range_without_line_numbers():
    lines = ["line1\n", "line2\n"]
    result = _format_line_range(0, 2, lines, line_numbers=False)
    assert "line1" in result
    assert "line2" in result
    assert "|" not in result


def test_compute_diff_modified_with_line_numbers():
    old_content = "line1\nline2\nline3\n"
    new_content = "line1\nchanged\nline3\n"
    result = compute_diff(old_content, new_content, "test.py", line_numbers=True)
    assert "2|" in result


def test_compute_diff_added_with_line_numbers():
    new_content = "line1\nline2\n"
    result = compute_diff("", new_content, "new.py", line_numbers=True)
    assert "1| line1" in result


def test_format_added_with_line_numbers():
    content = "line1\nline2\nline3\n"
    result = _format_added("new.py", content, "markdown", line_numbers=True)
    assert "    1| line1" in result
    assert "    2| line2" in result
    assert "    3| line3" in result


def test_format_added_with_line_numbers_empty_content():
    result = _format_added("empty.py", "", "markdown", line_numbers=True)
    assert "empty.py" in result


def test_compute_diff_no_line_numbers_default():
    old_content = "line1\nline2\n"
    new_content = "line1\nchanged\n"
    result = compute_diff(old_content, new_content, "test.py")
    assert "|" not in result


def test_format_added_with_line_numbers_xml():
    content = "line1\nline2\n"
    result = _format_added("new.py", content, "xml", line_numbers=True)
    assert "1| line1" in result


def test_compute_diff_deleted_with_line_numbers():
    old_content = "line1\nline2\n"
    result = compute_diff(old_content, "", "gone.py", line_numbers=True)
    assert "[DELETED]" in result


def test_format_line_range_single_line_numbers():
    lines = ["only line\n"]
    result = _format_line_range(0, 1, lines, line_numbers=True)
    assert "    1| only line" in result
