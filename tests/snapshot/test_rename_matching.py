"""Direct unit tests for _match_exact_renames and _match_similar_renames."""

import math

from arachna.snapshot.snapshots import _match_exact_renames, _match_similar_renames


def test_match_exact_renames_simple_rename():
    deleted = {"old.py": "same content"}
    added = {"new.py": "same content"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, added
    )
    assert len(sections) == 1
    assert sections[0].type == "renamed"
    assert sections[0].old_path == "old.py"
    assert sections[0].path == "new.py"
    assert math.isclose(sections[0].similarity, 1.0)
    assert "old.py" in matched_del
    assert "new.py" in matched_add
    assert remaining_del == {}
    assert remaining_add == {}


def test_match_exact_renames_same_dir_move():
    deleted = {"src/old/utils.py": "same content"}
    added = {"lib/utils.py": "same content"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, added
    )
    assert len(sections) == 1
    assert sections[0].type == "moved"
    assert sections[0].old_path == "src/old/utils.py"
    assert sections[0].path == "lib/utils.py"
    assert math.isclose(sections[0].similarity, 1.0)
    assert "src/old/utils.py" in matched_del
    assert "lib/utils.py" in matched_add


def test_match_exact_renames_move_and_rename():
    deleted = {"src/old.py": "same content"}
    added = {"lib/new.py": "same content"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, added
    )
    assert len(sections) == 1
    assert sections[0].type == "renamed"
    assert "MOVED AND RENAMED" in sections[0].content
    assert math.isclose(sections[0].similarity, 1.0)
    assert "src/old.py" in matched_del
    assert "lib/new.py" in matched_add


def test_match_exact_renames_same_path_same_hash_skipped():
    deleted = {"same.py": "unchanged"}
    added = {"same.py": "unchanged"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, added
    )
    assert len(sections) == 0
    assert "same.py" in matched_del
    assert "same.py" in matched_add
    assert remaining_del == {}
    assert remaining_add == {}


def test_match_exact_renames_ambiguous_one_deleted_two_added():
    deleted = {"old.py": "same"}
    added = {"new1.py": "same", "new2.py": "same"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, added
    )
    assert len(sections) == 0
    assert "old.py" in matched_del
    assert "new1.py" in matched_add
    assert "new2.py" in matched_add


def test_match_exact_renames_ambiguous_two_deleted_one_added():
    deleted = {"a.py": "same", "b.py": "same"}
    added = {"c.py": "same"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, added
    )
    assert len(sections) == 0
    assert "a.py" in matched_del
    assert "b.py" in matched_del
    assert "c.py" in matched_add


def test_match_exact_renames_no_match_different_hash():
    deleted = {"old.py": "content A"}
    added = {"new.py": "content B"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, added
    )
    assert len(sections) == 0
    assert matched_del == set()
    assert matched_add == set()
    assert "old.py" in remaining_del
    assert "new.py" in remaining_add


def test_match_exact_renames_empty_inputs():
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames({}, {})
    assert len(sections) == 0
    assert matched_del == set()
    assert matched_add == set()
    assert remaining_del == {}
    assert remaining_add == {}


def test_match_exact_renames_only_deleted():
    deleted = {"gone.py": "content"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, {}
    )
    assert len(sections) == 0
    assert remaining_del == {"gone.py": "content"}
    assert remaining_add == {}


def test_match_exact_renames_only_added():
    added = {"new.py": "content"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        {}, added
    )
    assert len(sections) == 0
    assert remaining_del == {}
    assert remaining_add == {"new.py": "content"}


def test_match_similar_renames_high_similarity():
    """Same directory, different name → RENAMED."""
    remaining_del = {
        "src/old.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    }
    remaining_add = {
        "src/new.py": "line1\nline2\nCHANGED\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    }
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 1
    assert sections[0].type == "renamed"
    assert sections[0].old_path == "src/old.py"
    assert sections[0].path == "src/new.py"
    assert sections[0].similarity is not None
    assert sections[0].similarity > 0.7
    assert "src/old.py" in matched_del
    assert "src/new.py" in matched_add


def test_match_similar_renames_moved():
    """Different directory, same name → MOVED."""
    remaining_del = {
        "src/utils.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    }
    remaining_add = {
        "lib/utils.py": "line1\nline2\nCHANGED\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    }
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 1
    assert sections[0].type == "moved"
    assert sections[0].old_path == "src/utils.py"
    assert sections[0].path == "lib/utils.py"
    assert sections[0].similarity is not None
    assert sections[0].similarity > 0.7
    assert "src/utils.py" in matched_del
    assert "lib/utils.py" in matched_add


def test_match_similar_renames_move_and_rename():
    """Different directory, different name → MOVED AND RENAMED."""
    remaining_del = {
        "src/old_handler.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    }
    remaining_add = {
        "lib/new_service.py": "line1\nline2\nCHANGED\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    }
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 1
    assert sections[0].type == "renamed"
    assert "MOVED AND RENAMED" in sections[0].content
    assert sections[0].old_path == "src/old_handler.py"
    assert sections[0].path == "lib/new_service.py"
    assert sections[0].similarity is not None
    assert sections[0].similarity > 0.7
    assert "src/old_handler.py" in matched_del
    assert "lib/new_service.py" in matched_add


def test_match_similar_renames_below_threshold():
    remaining_del = {"old.py": "completely different content here yes"}
    remaining_add = {"new.py": "nothing in common with the old file at all"}
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 0


def test_match_similar_renames_binary_content_skipped():
    remaining_del = {"data.bin": "text\x00binary"}
    remaining_add = {"data2.bin": "text\x00binary"}
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 0


def test_match_similar_renames_binary_content_in_added_skipped():
    remaining_del = {"old.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\n"}
    remaining_add = {"new.py": "text\x00binary"}
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 0
