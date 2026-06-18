"""Tests for public Snapshot API - compute_diff, store operations (v2.0.0)."""

import pytest

from arachna.api.api_errors import ProfileNotFoundError, SnapshotNotFoundError
from arachna.api.snapshot import (
    compute_diff,
    create_snapshot,
    snapshot_info,
    store_gc,
    store_stats,
    update_snapshot,
)


def test_api_compute_diff_modified(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="diff-snap")
    (src / "a.py").write_text("modified")
    result = compute_diff(root=root, snapshot_id="diff-snap", profile=profile)
    assert result.stats.modified >= 1
    assert any(s.type == "modified" for s in result.sections if s.path)


def test_api_compute_diff_no_changes(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("same")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="no-changes")
    result = compute_diff(root=root, snapshot_id="no-changes", profile=profile)
    assert result.stats.modified == 0


def test_api_compute_diff_auto_select(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="auto-snap")
    result = compute_diff(root=root, profile=profile)
    assert result.snapshot_id == "auto-snap"


def test_api_compute_diff_no_snapshots(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")
    profile = make_profile("src", ["*.py"])
    with pytest.raises(SnapshotNotFoundError):
        compute_diff(root=root, profile=profile)


def test_api_compute_diff_multiple_snapshots_raises(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="s1")
    create_snapshot(root=root, profile=profile, name="s2")
    with pytest.raises(ValueError):
        compute_diff(root=root, profile=profile)


def test_api_compute_diff_cross_snapshot(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("v1")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="v1")
    (src / "a.py").write_text("v2")
    create_snapshot(root=root, profile=profile, name="v2")
    result = compute_diff(root=root, snapshot_id="v1", profile=profile, to_snapshot_id="v2")
    assert result.stats.modified >= 1


def test_api_compute_diff_structural_mode(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("def foo():\n    return 1\n")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="struct-snap")
    (src / "a.py").write_text("def foo():\n    return 2\n")
    result = compute_diff(root=root, snapshot_id="struct-snap", profile=profile, mode="structural")
    assert result.stats.modified >= 1


def test_api_compute_diff_repo_map_mode(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("def foo():\n    return 1\n\ndef bar():\n    return 2\n")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="rm-snap")
    (src / "a.py").write_text("def foo():\n    return 3\n\ndef bar():\n    return 4\n")
    result = compute_diff(root=root, snapshot_id="rm-snap", profile=profile, mode="repo-map")
    assert result.stats.modified >= 1


def test_api_compute_diff_profile_not_found(tmp_path, setup_config):
    root = setup_config(profiles={"x": {"command": "echo hi", "max_tokens": 100}})
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x")
    with pytest.raises(ProfileNotFoundError):
        compute_diff(root=root, profile="nonexistent", snapshot_id="no-such")


def test_api_update_snapshot_profile_dict(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="api-upd")
    (src / "a.py").write_text("modified")
    update_snapshot("api-upd", root=root, profile=profile)
    info = snapshot_info("api-upd", root=root)
    assert info.file_count == 1


def test_api_update_snapshot_profile_name(tmp_path, setup_config):
    root = setup_config(
        profiles={
            "code": {
                "directories": ["src"],
                "patterns": ["*.py"],
                "max_tokens": 16000,
                "split_mode": "by_file",
                "use_gitignore": False,
            }
        }
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    create_snapshot(root=root, profile="code", name="api-upd2")
    (src / "a.py").write_text("modified")
    update_snapshot("api-upd2", root=root, profile="code")


def test_api_update_snapshot_not_found(tmp_path, setup_config, make_profile):
    root = setup_config()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x")
    profile = make_profile("src", ["*.py"])
    with pytest.raises(SnapshotNotFoundError):
        update_snapshot("nonexistent", root=root, profile=profile)


def test_api_update_snapshot_profile_not_found(tmp_path, setup_config, make_profile):
    root = setup_config(profiles={"x": {"command": "echo hi", "max_tokens": 100}})
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="api-upd3")
    with pytest.raises(ProfileNotFoundError):
        update_snapshot("api-upd3", root=root, profile="nonexistent")


def test_api_store_stats(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("hello")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="stats-test")
    stats = store_stats(root=root)
    assert stats.snapshots == 1
    assert stats.objects >= 1


def test_api_store_stats_empty(tmp_path, setup_config):
    root = setup_config()
    stats = store_stats(root=root)
    assert stats.snapshots == 0
    assert stats.objects == 0


def test_api_store_gc(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("hello")
    profile = make_profile("src", ["*.py"])
    create_snapshot(root=root, profile=profile, name="gc-test")
    result = store_gc(root=root)
    assert result.removed_objects >= 0
    assert result.freed_bytes >= 0
