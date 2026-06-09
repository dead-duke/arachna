"""Tests for cross-snapshot diff in watcher.py (v1.7.0)."""

import json

from arachna.watcher import (
    _build_current_files,
    _diff_file_sets,
    _get_content_from_manifest,
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


def test_cross_snapshot_diff_modified(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("version 1")
    profile = _make_profile("src", ["*.py"])
    sid1 = create_snapshot(profile, name="v1")
    (src / "main.py").write_text("version 2")
    sid2 = create_snapshot(profile, name="v2")
    diffs = compute_diff(sid1, profile, to_snapshot_id=sid2)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1
    assert content_diffs[0].type == "modified"
    assert content_diffs[0].path == "src/main.py"


def test_cross_snapshot_diff_added(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("existing")
    profile = _make_profile("src", ["*.py"])
    sid1 = create_snapshot(profile, name="v1")
    (src / "b.py").write_text("new file")
    sid2 = create_snapshot(profile, name="v2")
    diffs = compute_diff(sid1, profile, to_snapshot_id=sid2)
    content_diffs = [d for d in diffs if d.type == "added" and d.path]
    assert len(content_diffs) >= 1
    added = [d for d in content_diffs if d.type == "added"]
    assert any("b.py" in d.path for d in added)


def test_cross_snapshot_diff_deleted(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("will be deleted")
    profile = _make_profile("src", ["*.py"])
    sid1 = create_snapshot(profile, name="v1")
    (src / "a.py").unlink()
    sid2 = create_snapshot(profile, name="v2")
    diffs = compute_diff(sid1, profile, to_snapshot_id=sid2)
    content_diffs = [d for d in diffs if d.type == "deleted" and d.path]
    assert len(content_diffs) >= 1


def test_cross_snapshot_diff_unchanged(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("unchanged")
    profile = _make_profile("src", ["*.py"])
    sid1 = create_snapshot(profile, name="v1")
    sid2 = create_snapshot(profile, name="v2")
    diffs = compute_diff(sid1, profile, to_snapshot_id=sid2)
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 0


def test_cross_snapshot_diff_same_snapshot(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("same")
    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="only")
    diffs = compute_diff(sid, profile, to_snapshot_id=sid)
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 0


def test_get_content_from_manifest(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    from arachna.store import write_object

    obj_hash = write_object(b"hello world")
    hash_spec = f"sha256:{obj_hash}"
    content = _get_content_from_manifest("test.txt", hash_spec)
    assert content == "hello world"


def test_build_current_files(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "utils.py").write_text("x = 1")
    profile = _make_profile("src", ["*.py"])
    files = _build_current_files(profile, [])
    assert len(files) == 2
    assert any("main.py" in f for f in files)
    assert any("utils.py" in f for f in files)


def test_diff_file_sets_modified(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    old_files = {"a.py": "old content"}
    new_files = {"a.py": "new content"}
    diffs = _diff_file_sets(old_files, new_files, "markdown")
    assert len(diffs) == 1
    assert diffs[0].type == "modified"
    assert diffs[0].path == "a.py"


def test_diff_file_sets_added():
    old_files = {}
    new_files = {"new.py": "hello"}
    diffs = _diff_file_sets(old_files, new_files, "markdown")
    assert len(diffs) == 1
    assert diffs[0].type == "added"


def test_diff_file_sets_deleted():
    old_files = {"old.py": "gone"}
    new_files = {}
    diffs = _diff_file_sets(old_files, new_files, "markdown")
    assert len(diffs) == 1
    assert diffs[0].type == "deleted"


def test_diff_file_sets_empty():
    diffs = _diff_file_sets({}, {}, "markdown")
    assert diffs == []
