"""Edge case for _fallback_diff with empty old and new content."""

from arachna.watch.differ_structural import _fallback_diff


def test_fallback_diff_both_empty():
    """_fallback_diff returns empty string when both old and new are empty."""
    result = _fallback_diff("", "", "empty.py", "markdown")
    assert result == ""


def test_fallback_diff_both_empty_xml():
    """_fallback_diff with xml format and both empty returns empty string."""
    result = _fallback_diff("", "", "empty.py", "xml")
    assert result == ""
