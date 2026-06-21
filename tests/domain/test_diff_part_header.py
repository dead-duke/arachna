"""Tests for _diff_part_header in collector.py (v2.8.2)."""

from arachna.domain.collection.collector import _diff_part_header


def test_diff_part_header_all_types():
    """Header shows all change types."""
    stats = {"renamed": 2, "moved": 1, "modified": 5, "added": 3, "deleted": 1}
    header = _diff_part_header(stats, 1, 3)
    assert "Part 1 of 3" in header
    assert "Changes: " in header
    assert "2 renamed" in header
    assert "1 moved" in header
    assert "5 modified" in header
    assert "3 added" in header
    assert "1 deleted" in header


def test_diff_part_header_no_changes():
    """Header shows 'no changes' when all zero."""
    stats = {"renamed": 0, "moved": 0, "modified": 0, "added": 0, "deleted": 0}
    header = _diff_part_header(stats, 2, 5)
    assert "Part 2 of 5" in header
    assert "no changes" in header


def test_diff_part_header_only_modified():
    """Header shows only non-zero change types."""
    stats = {"renamed": 0, "moved": 0, "modified": 3, "added": 0, "deleted": 0}
    header = _diff_part_header(stats, 3, 4)
    assert "3 modified" in header
    assert "renamed" not in header
    assert "added" not in header
