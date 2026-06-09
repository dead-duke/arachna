"""Tests for rename/move detection in watcher.py (v1.7.0)."""

import json

from arachna.watcher import (
    _detect_renames_and_moves,
    _diff_file_sets,
    _is_binary_content,
    compute_diff,
    create_snapshot,
)


def _make_profile(directory: str, patterns=None, files=None) -> dict:
    return {
        "directories": [directory],
        "patterns": patterns or ["*"],
        "files": files or [],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


def _setup_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )


def test_rename_exact_same_content(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "old_name.py").write_text("print('hello')")
    profile = _make_profile("src", ["*.py"])
    sid1 = create_snapshot(profile, name="v1")
    (src / "old_name.py").unlink()
    (src / "new_name.py").write_text("print('hello')")
    sid2 = create_snapshot(profile, name="v2")
    diffs = compute_diff(sid1, profile, to_snapshot_id=sid2)
    content_diffs = [d for d in diffs if d.type == "renamed" and d.path]
    assert len(content_diffs) == 1, f"Expected 1 renamed, got {content_diffs}"
    assert content_diffs[0].old_path == "src/old_name.py"
    assert content_diffs[0].path == "src/new_name.py"
    assert content_diffs[0].similarity == 1.0


def test_move_exact_same_content(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    lib = tmp_path / "lib"
    lib.mkdir()
    (src / "utils.py").write_text("def helper(): pass")
    profile = _make_profile("src", ["*.py"])
    sid1 = create_snapshot(profile, name="v1")
    (src / "utils.py").unlink()
    profile2 = {
        "directories": ["lib"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }
    (lib / "utils.py").write_text("def helper(): pass")
    sid2 = create_snapshot(profile2, name="v2")
    diffs = compute_diff(sid1, profile2, to_snapshot_id=sid2)
    content_diffs = [d for d in diffs if d.type == "moved" and d.path]
    assert len(content_diffs) >= 1, f"Expected moved in {[d.type for d in diffs]}"


def test_rename_similar_content(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "old.py").write_text(
        "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    )
    profile = _make_profile("src", ["*.py"])
    sid1 = create_snapshot(profile, name="v1")
    (src / "old.py").unlink()
    (src / "new.py").write_text(
        "line1\nline2\nCHANGED\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n"
    )
    sid2 = create_snapshot(profile, name="v2")
    diffs = compute_diff(sid1, profile, to_snapshot_id=sid2)
    content_diffs = [d for d in diffs if d.type == "renamed" and d.path]
    assert len(content_diffs) >= 1, f"Expected renamed in {[d.type for d in diffs]}"


def test_dissimilar_no_rename(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "old.py").write_text("completely different content here yes")
    profile = _make_profile("src", ["*.py"])
    sid1 = create_snapshot(profile, name="v1")
    (src / "old.py").unlink()
    (src / "new.py").write_text("nothing in common with the old file at all")
    sid2 = create_snapshot(profile, name="v2")
    diffs = compute_diff(sid1, profile, to_snapshot_id=sid2)
    content_diffs = [d for d in diffs if d.path]
    types = [d.type for d in content_diffs]
    assert "deleted" in types
    assert "added" in types
    assert "renamed" not in types


def test_binary_no_similarity_check(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "data.bin").write_bytes(b"\x00\x01\x02\x03")
    profile = _make_profile("src", ["*"])
    sid1 = create_snapshot(profile, name="v1")
    (src / "data.bin").unlink()
    (src / "moved.bin").write_bytes(b"\x00\x01\x02\x03")
    sid2 = create_snapshot(profile, name="v2")
    diffs = compute_diff(sid1, profile, to_snapshot_id=sid2)
    content_diffs = [d for d in diffs if d.type == "renamed" and d.path]
    assert len(content_diffs) >= 1


def test_is_binary_content():
    assert _is_binary_content("text\x00binary")
    assert not _is_binary_content("plain text")
    assert not _is_binary_content("")


def test_detect_renames_and_moves_basic():
    deleted = {"old.py": "same content"}
    added = {"new.py": "same content"}
    sections, matched_del, matched_add = _detect_renames_and_moves(deleted, added, "markdown")
    assert len(sections) == 1
    assert sections[0].type == "renamed"
    assert sections[0].similarity == 1.0
    assert "old.py" in matched_del
    assert "new.py" in matched_add


def test_detect_renames_and_moves_same_path_skipped():
    deleted = {"same.py": "content"}
    added = {"same.py": "content"}
    sections, matched_del, matched_add = _detect_renames_and_moves(deleted, added, "markdown")
    assert len(sections) == 0


def test_detect_renames_and_moves_multiple_same_hash():
    deleted = {"a.py": "same", "b.py": "same"}
    added = {"c.py": "same"}
    sections, matched_del, matched_add = _detect_renames_and_moves(deleted, added, "markdown")
    assert len(sections) == 0


def test_detect_renames_and_moves_similar():
    deleted = {"old.py": "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\n"}
    added = {"new.py": "line1\nline2\nCHANGED\nline4\nline5\nline6\nline7\nline8\n"}
    sections, matched_del, matched_add = _detect_renames_and_moves(deleted, added, "markdown")
    assert len(sections) == 1
    assert sections[0].type == "renamed"
    assert sections[0].similarity is not None
    assert sections[0].similarity > 0.7


def test_detect_renames_and_moves_dissimilar():
    deleted = {"old.py": "totally different"}
    added = {"new.py": "nothing in common"}
    sections, matched_del, matched_add = _detect_renames_and_moves(deleted, added, "markdown")
    assert len(sections) == 0


def test_diff_file_sets_handles_rename(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    old_files = {"src/old.py": "unchanged content here yes"}
    new_files = {"src/new.py": "unchanged content here yes"}
    diffs = _diff_file_sets(old_files, new_files, "markdown")
    types = [d.type for d in diffs]
    assert "renamed" in types
    assert "deleted" not in types
    assert "added" not in types
