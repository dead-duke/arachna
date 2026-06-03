"""Tests for watcher orchestration layer."""

from arachna.store import load_snapshot
from arachna.watcher import compute_diff, create_snapshot


def _make_profile(directory: str, patterns: list[str] | None = None) -> dict:
    """Helper to create a minimal profile dict."""
    return {
        "directories": [directory],
        "patterns": patterns or ["*"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


def test_create_snapshot_returns_id(tmp_path, monkeypatch):
    """create_snapshot returns a snapshot ID."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="test-snap")
    assert sid == "test-snap"


def test_create_snapshot_stores_files(tmp_path, monkeypatch):
    """create_snapshot stores file contents in manifest."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "utils.py").write_text("def foo(): pass")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="files-snap")

    manifest = load_snapshot(sid)
    assert len(manifest["files"]) == 2
    assert any("main.py" in f for f in manifest["files"])
    assert any("utils.py" in f for f in manifest["files"])


def test_compute_diff_modified(tmp_path, monkeypatch):
    """Modified file is detected."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    # Modify the file
    (src / "a.py").write_text("modified")

    diffs = compute_diff(sid, profile)
    assert len(diffs) == 1
    assert diffs[0].type == "modified"
    assert diffs[0].path == "src/a.py"


def test_compute_diff_added(tmp_path, monkeypatch):
    """New file is detected as added."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("existing")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    # Add new file
    (src / "b.py").write_text("new file")

    diffs = compute_diff(sid, profile)
    assert len(diffs) == 1
    assert diffs[0].type == "added"
    assert diffs[0].path == "src/b.py"


def test_compute_diff_deleted(tmp_path, monkeypatch):
    """Deleted file is detected."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("to be deleted")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    # Delete the file
    (src / "a.py").unlink()

    diffs = compute_diff(sid, profile)
    assert len(diffs) == 1
    assert diffs[0].type == "deleted"
    assert diffs[0].path == "src/a.py"


def test_compute_diff_unchanged(tmp_path, monkeypatch):
    """Unchanged file produces no diff."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("unchanged")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    diffs = compute_diff(sid, profile)
    assert len(diffs) == 0


def test_compute_diff_profile_change_ignored(tmp_path, monkeypatch):
    """File removed from profile is not reported as deleted."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("keep")
    (src / "b.py").write_text("remove from profile")

    # Snapshot with both files
    profile_both = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile_both, name="snap1")

    # New profile only collects a.py
    profile_a = _make_profile("src", ["a.py"])

    diffs = compute_diff(sid, profile_a)
    # b.py is gone from disk AND from profile → ignored
    # a.py unchanged → no diff
    assert len(diffs) == 0
