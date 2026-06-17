"""Direct unit tests for _match_exact_renames and _match_similar_renames.

These functions were decomposed from _detect_renames_and_moves in v3.4.0.
Previously tested only indirectly through _detect_renames_and_moves.
"""

import math

from arachna.watch.watcher import _match_exact_renames, _match_similar_renames

# -- _match_exact_renames -------------------------------------------------


def test_match_exact_renames_simple_rename():
    """Same content, different name, same directory -> renamed."""
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
    """Same content, same name, different directory -> moved."""
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
    """Same content, different name, different directory -> moved and renamed."""
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
    """Same path and same hash in both deleted and added -> skipped, not a rename."""
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
    """One deleted, two added with same hash -> ambiguous, no rename."""
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
    """Two deleted with same hash, one added -> ambiguous, no rename."""
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
    """Different hash -> no rename, files remain in remaining dicts."""
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


def test_match_exact_renames_no_match_empty_opposite():
    """No overlap in hashes -> all files remain."""
    deleted = {"old.py": "content A"}
    added = {"new.py": "content B"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, added
    )
    assert len(sections) == 0
    assert remaining_del == {"old.py": "content A"}
    assert remaining_add == {"new.py": "content B"}


def test_match_exact_renames_empty_inputs():
    """Empty deleted and added -> empty result."""
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames({}, {})
    assert len(sections) == 0
    assert matched_del == set()
    assert matched_add == set()
    assert remaining_del == {}
    assert remaining_add == {}


def test_match_exact_renames_only_deleted():
    """Only deleted files, no added -> all remain as deleted."""
    deleted = {"gone.py": "content"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, {}
    )
    assert len(sections) == 0
    assert remaining_del == {"gone.py": "content"}
    assert remaining_add == {}


def test_match_exact_renames_only_added():
    """Only added files, no deleted -> all remain as added."""
    added = {"new.py": "content"}
    sections, matched_del, matched_add, remaining_del, remaining_add = _match_exact_renames(
        {}, added
    )
    assert len(sections) == 0
    assert remaining_del == {}
    assert remaining_add == {"new.py": "content"}


# -- _match_similar_renames -------------------------------------------------


def test_match_similar_renames_high_similarity():
    """Content >70% similar with same extension -> rename detected."""
    remaining_del = {
        "old.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    }
    remaining_add = {
        "new.py": "line1\nline2\nCHANGED\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    }
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 1
    assert sections[0].type == "renamed"
    assert sections[0].old_path == "old.py"
    assert sections[0].path == "new.py"
    assert sections[0].similarity is not None
    assert sections[0].similarity > 0.7
    assert "old.py" in matched_del
    assert "new.py" in matched_add


def test_match_similar_renames_move_same_name():
    """Same name, different dir, similar content -> moved."""
    remaining_del = {"src/utils.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\n"}
    remaining_add = {"lib/utils.py": "line1\nline2\nline3\nline4\nline5\nCHANGED\nline7\nline8\n"}
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 1
    assert sections[0].type == "moved"
    assert sections[0].old_path == "src/utils.py"
    assert sections[0].path == "lib/utils.py"


def test_match_similar_renames_move_and_rename():
    """Different name, different dir, similar content -> moved and renamed."""
    remaining_del = {"src/old.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\n"}
    remaining_add = {"lib/new.py": "line1\nline2\nCHANGED\nline4\nline5\nline6\nline7\nline8\n"}
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 1
    assert sections[0].type == "renamed"
    assert "MOVED AND RENAMED" in sections[0].content


def test_match_similar_renames_below_threshold():
    """Content <70% similar -> no rename."""
    remaining_del = {"old.py": "completely different content here yes"}
    remaining_add = {"new.py": "nothing in common with the old file at all"}
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 0
    assert matched_del == set()
    assert matched_add == set()


def test_match_similar_renames_different_extension():
    """Different extension -> not considered for similarity matching."""
    remaining_del = {"old.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\n"}
    remaining_add = {"new.js": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\n"}
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 0


def test_match_similar_renames_already_matched_in_added():
    """File already in matched_added set -> skipped."""
    remaining_del = {"old.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\n"}
    remaining_add = {"new.py": "line1\nline2\nCHANGED\nline4\nline5\nline6\nline7\nline8\n"}
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, {"new.py"}, "markdown"
    )
    assert len(sections) == 0


def test_match_similar_renames_empty_inputs():
    """Empty dicts -> empty result."""
    sections, matched_del, matched_add = _match_similar_renames({}, {}, set(), "markdown")
    assert len(sections) == 0


def test_match_similar_renames_binary_content_skipped():
    """Binary content (null byte) in deleted -> skipped for similarity check."""
    remaining_del = {"data.bin": "text\x00binary"}
    remaining_add = {"data2.bin": "text\x00binary"}
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 0


def test_match_similar_renames_first_match_wins():
    """Multiple candidates for similarity -> first match above 0.7 wins."""
    remaining_del = {"old.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\n"}
    remaining_add = {
        "candidate1.py": "line1\nline2\nCHANGED\nline4\nline5\nline6\nline7\nline8\n",
        "candidate2.py": "line1\nline2\nline3\nline4\nline5\nCHANGED\nline7\nline8\n",
    }
    sections, matched_del, matched_add = _match_similar_renames(
        remaining_del, remaining_add, set(), "markdown"
    )
    assert len(sections) == 1
    assert "old.py" in matched_del
    assert len(matched_add) == 1
