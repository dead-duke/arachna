"""Edge case tests for differ.py uncovered branches."""

from arachna.snapshot.differ import _format_line_range, compute_diff


def test_format_line_range_start_equals_end():
    """_format_line_range returns empty string when start == end."""
    result = _format_line_range(3, 3, ["line1\n", "line2\n", "line3\n"])
    assert result == ""


def test_format_line_range_single_line():
    """_format_line_range with a single line range."""
    result = _format_line_range(1, 2, ["line1\n", "line2\n", "line3\n"])
    assert "lines 2" in result
    assert "line2" in result


def test_format_line_range_multi_line():
    """_format_line_range with multiple lines shows line range."""
    result = _format_line_range(0, 3, ["a\n", "b\n", "c\n", "d\n"])
    assert "lines 1-3" in result
    assert "a" in result
    assert "b" in result
    assert "c" in result


def test_compute_diff_delete_only():
    """Only deleted lines produce REMOVED block with no ADDED."""
    old_content = "line1\nline2\nline3\n"
    new_content = "line2\n"
    result = compute_diff(old_content, new_content, "test.py")
    assert "REMOVED" in result
    assert "ADDED" not in result


def test_compute_diff_insert_only():
    """Only inserted lines produce ADDED block with no REMOVED."""
    old_content = "line2\n"
    new_content = "line1\nline2\nline3\n"
    result = compute_diff(old_content, new_content, "test.py")
    assert "ADDED" in result
    assert "REMOVED" not in result


def test_compute_diff_empty_after_filter():
    """When all blocks filtered to empty, returns empty string."""
    result = compute_diff("line1\n", "line1\n", "test.py")
    assert result == ""
