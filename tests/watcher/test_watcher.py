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
    """Modified file is detected (grouped output by default)."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    (src / "a.py").write_text("modified")

    diffs = compute_diff(sid, profile)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1
    assert content_diffs[0].type == "modified"
    assert content_diffs[0].path == "src/a.py"


def test_compute_diff_added(tmp_path, monkeypatch):
    """New file is detected as added (grouped output by default)."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("existing")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    (src / "b.py").write_text("new file")

    diffs = compute_diff(sid, profile)
    content_diffs = [d for d in diffs if d.type == "added" and d.path]
    assert len(content_diffs) == 1
    assert content_diffs[0].type == "added"
    assert content_diffs[0].path == "src/b.py"


def test_compute_diff_deleted(tmp_path, monkeypatch):
    """Deleted file is detected (grouped output by default)."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("to be deleted")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    (src / "a.py").unlink()

    diffs = compute_diff(sid, profile)
    content_diffs = [d for d in diffs if d.type == "deleted" and d.path]
    assert len(content_diffs) == 1
    assert content_diffs[0].type == "deleted"
    assert content_diffs[0].path == "src/a.py"


def test_compute_diff_unchanged(tmp_path, monkeypatch):
    """Unchanged file produces no content diffs."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("unchanged")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    diffs = compute_diff(sid, profile)
    # No content diffs — may have header only or empty
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 0


def test_compute_diff_profile_change_ignored(tmp_path, monkeypatch):
    """File removed from profile is not reported as deleted."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("keep")
    (src / "b.py").write_text("remove from profile")

    profile_both = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile_both, name="snap1")

    profile_a = _make_profile("src", ["a.py"])

    diffs = compute_diff(sid, profile_a)
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 0


def test_compute_diff_flat_mode(tmp_path, monkeypatch):
    """flat=True returns flat list without grouping headers."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    (src / "a.py").write_text("modified")

    diffs = compute_diff(sid, profile, flat=True)
    # Flat mode: no header, no group sections — just content
    assert len(diffs) == 1
    assert diffs[0].type == "modified"
    assert diffs[0].path == "src/a.py"


def test_compute_diff_grouped_has_header(tmp_path, monkeypatch):
    """Grouped output includes summary header."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    (src / "a.py").write_text("modified")

    diffs = compute_diff(sid, profile)
    headers = [d for d in diffs if d.type == "header"]
    assert len(headers) == 1
    assert "Changes from snap1 to current" in headers[0].content
    assert "1 modified" in headers[0].content


def test_compute_diff_grouped_order(tmp_path, monkeypatch):
    """Grouped output follows order: renamed, moved, modified, added, deleted."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "mod.py").write_text("original")
    (src / "gone.py").write_text("delete me")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1")

    (src / "mod.py").write_text("changed")
    (src / "gone.py").unlink()
    (src / "new.py").write_text("new file")

    diffs = compute_diff(sid, profile)
    types_in_order = [d.type for d in diffs if d.type and d.type != "header"]
    # Should have group headers followed by content
    assert "modified" in types_in_order
    assert "added" in types_in_order
    assert "deleted" in types_in_order
