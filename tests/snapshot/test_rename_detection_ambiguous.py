"""Test _detect_renames_and_moves with ambiguous hash cases."""

from arachna.snapshot.rename.snapshot_rename import _detect_renames_and_moves


def test_multiple_same_hash_deleted_single_added():
    deleted = {"a.py": "same", "b.py": "same"}
    added = {"c.py": "same"}
    sections, matched_del, matched_add = _detect_renames_and_moves(deleted, added, "markdown")
    assert len(sections) == 0


def test_single_deleted_multiple_same_hash_added():
    deleted = {"old.py": "same"}
    added = {"new1.py": "same", "new2.py": "same"}
    sections, matched_del, matched_add = _detect_renames_and_moves(deleted, added, "markdown")
    assert len(sections) == 0


def test_multiple_same_hash_both_sides():
    deleted = {"a.py": "same", "b.py": "same"}
    added = {"c.py": "same", "d.py": "same"}
    sections, matched_del, matched_add = _detect_renames_and_moves(deleted, added, "markdown")
    assert len(sections) == 0


def test_same_path_same_hash_skipped():
    deleted = {"same.py": "content"}
    added = {"same.py": "content"}
    sections, matched_del, matched_add = _detect_renames_and_moves(deleted, added, "markdown")
    assert len(sections) == 0
    assert "same.py" in matched_del
    assert "same.py" in matched_add
