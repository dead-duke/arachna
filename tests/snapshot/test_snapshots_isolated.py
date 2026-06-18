"""Isolated unit tests for snapshot helper functions (v2.9.2)."""

from arachna.domain.api_types import DiffSection
from arachna.snapshot.snapshots import (
    _detect_renames_and_moves,
    _diff_pre_commands_line,
    _diff_pre_commands_marker,
    _format_summary_header,
    _group_diff_sections,
)


def test_format_summary_header_all_types():
    stats = {"renamed": 2, "moved": 1, "modified": 5, "added": 3, "deleted": 1}
    header = _format_summary_header(stats, "snap1", "snap2")
    assert "Changes from snap1 to snap2" in header
    assert "2 renamed" in header
    assert "1 moved" in header
    assert "5 modified" in header
    assert "3 added" in header
    assert "1 deleted" in header


def test_format_summary_header_no_changes():
    stats = {"renamed": 0, "moved": 0, "modified": 0, "added": 0, "deleted": 0}
    header = _format_summary_header(stats, "snap1", None)
    assert "No changes" in header


def test_group_diff_sections_order():
    sections = [
        DiffSection(type="deleted", path="d.py", content="[DELETED]"),
        DiffSection(type="modified", path="a.py", content="diff"),
        DiffSection(type="added", path="c.py", content="new"),
        DiffSection(type="modified", path="b.py", content="diff2"),
    ]
    grouped = _group_diff_sections(sections, "snap1", "current")
    types = [s.type for s in grouped if s.type != "header"]
    assert types[0] == "modified"
    assert types[1] == "modified"
    assert "added" in types
    assert "deleted" in types


def test_group_diff_sections_empty():
    assert _group_diff_sections([], "snap1", None) == []


def test_diff_pre_commands_line_added():
    old = "src/main.py\n"
    new = "src/main.py\nsrc/new.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "+ src/new.py" in result


def test_diff_pre_commands_line_deleted():
    old = "src/main.py\nsrc/old.py\n"
    new = "src/main.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "- src/old.py" in result


def test_diff_pre_commands_line_unchanged():
    result = _diff_pre_commands_line("same\n", "same\n", "pre: test")
    assert result == ""


def test_diff_pre_commands_marker_modified():
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: abc ===\nold\n"
    new = "=== COMMIT: abc ===\nnew\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "REMOVED" in result or "ADDED" in result


def test_diff_pre_commands_marker_added():
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: a ===\nmsg\n"
    new = "=== COMMIT: a ===\nmsg\n\n=== COMMIT: b ===\nnew\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "section 2" in result


def test_diff_pre_commands_marker_deleted():
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: a ===\n1\n\n=== COMMIT: b ===\n2\n"
    new = "=== COMMIT: a ===\n1\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "DELETED" in result


def test_detect_renames_and_moves_exact_hash():
    deleted = {"old.py": "same"}
    added = {"new.py": "same"}
    sections, matched_del, matched_add = _detect_renames_and_moves(deleted, added, "markdown")
    assert len(sections) == 1
    assert sections[0].type == "renamed"
    assert sections[0].similarity == 1.0
