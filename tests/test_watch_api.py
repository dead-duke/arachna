"""Tests for public Watch API — compute_diff, store operations (v2.0.0)."""

import json

import pytest

from arachna.api_errors import ProfileNotFoundError, SnapshotNotFoundError
from arachna.watch import (
    compute_diff,
    create_snapshot,
    snapshot_info,
    store_gc,
    store_stats,
    update_snapshot,
)


def _make_profile(directory: str, patterns=None) -> dict:
    return {
        "directories": [directory],
        "patterns": patterns or ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


# ── compute_diff ───────────────────────────────────────────────────


def test_api_compute_diff_modified(tmp_path, monkeypatch):
    """compute_diff detects modified file."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="diff-snap")
    (src / "a.py").write_text("modified")

    result = compute_diff(snapshot_id="diff-snap", profile=profile)
    # Grouped output includes header + modified sections → at least 1 modified
    assert result.stats.modified >= 1
    assert any(s.type == "modified" for s in result.sections if s.path)


def test_api_compute_diff_no_changes(tmp_path, monkeypatch):
    """compute_diff with unchanged files returns zero stats."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("same")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="no-changes")

    result = compute_diff(snapshot_id="no-changes", profile=profile)
    assert result.stats.modified == 0


def test_api_compute_diff_auto_select(tmp_path, monkeypatch):
    """compute_diff auto-selects single snapshot."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="auto-snap")

    result = compute_diff(profile=profile)
    assert result.snapshot_id == "auto-snap"


def test_api_compute_diff_no_snapshots(tmp_path, monkeypatch):
    """compute_diff with no snapshots raises SnapshotNotFoundError."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")

    profile = _make_profile("src")
    with pytest.raises(SnapshotNotFoundError):
        compute_diff(profile=profile)


def test_api_compute_diff_multiple_snapshots_raises(tmp_path, monkeypatch):
    """compute_diff with multiple snapshots and no snapshot_id raises ValueError."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="s1")
    create_snapshot(profile=profile, name="s2")

    with pytest.raises(ValueError):
        compute_diff(profile=profile)


def test_api_compute_diff_cross_snapshot(tmp_path, monkeypatch):
    """compute_diff with to_snapshot_id does cross-snapshot diff."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("v1")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="v1")
    (src / "a.py").write_text("v2")
    create_snapshot(profile=profile, name="v2")

    result = compute_diff(snapshot_id="v1", profile=profile, to_snapshot_id="v2")
    assert result.stats.modified >= 1


def test_api_compute_diff_structural_mode(tmp_path, monkeypatch):
    """compute_diff with mode='structural' applies structural diff."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("def foo():\n    return 1\n")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="struct-snap")
    (src / "a.py").write_text("def foo():\n    return 2\n")

    result = compute_diff(snapshot_id="struct-snap", profile=profile, mode="structural")
    assert result.stats.modified >= 1


def test_api_compute_diff_repo_map_mode(tmp_path, monkeypatch):
    """compute_diff with mode='repo-map' extracts signatures."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("def foo():\n    return 1\n\ndef bar():\n    return 2\n")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="rm-snap")
    (src / "a.py").write_text("def foo():\n    return 3\n\ndef bar():\n    return 4\n")

    result = compute_diff(snapshot_id="rm-snap", profile=profile, mode="repo-map")
    assert result.stats.modified >= 1


def test_api_compute_diff_profile_not_found(tmp_path, monkeypatch):
    """compute_diff with unknown profile name raises ProfileNotFoundError."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}})
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x")

    with pytest.raises(ProfileNotFoundError):
        compute_diff(profile="nonexistent", snapshot_id="no-such")


# ── update_snapshot via API ────────────────────────────────────────


def test_api_update_snapshot_profile_dict(tmp_path, monkeypatch):
    """update_snapshot with profile dict works."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="api-upd")

    (src / "a.py").write_text("modified")
    update_snapshot("api-upd", profile=profile)

    info = snapshot_info("api-upd")
    assert info.file_count == 1


def test_api_update_snapshot_profile_name(tmp_path, monkeypatch):
    """update_snapshot with profile name works."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                }
            }
        )
    )

    create_snapshot(profile="code", name="api-upd2")
    (src / "a.py").write_text("modified")
    update_snapshot("api-upd2", profile="code")


def test_api_update_snapshot_not_found(tmp_path, monkeypatch):
    """update_snapshot with non-existent snapshot raises SnapshotNotFoundError."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x")

    profile = _make_profile("src")
    with pytest.raises(SnapshotNotFoundError):
        update_snapshot("nonexistent", profile=profile)


def test_api_update_snapshot_profile_not_found(tmp_path, monkeypatch):
    """update_snapshot with unknown profile name raises ProfileNotFoundError."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}})
    )

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="api-upd3")

    with pytest.raises(ProfileNotFoundError):
        update_snapshot("api-upd3", profile="nonexistent")


# ── store operations ───────────────────────────────────────────────


def test_api_store_stats(tmp_path, monkeypatch):
    """store_stats returns StoreStats."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("hello")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="stats-test")

    stats = store_stats()
    assert stats.snapshots == 1
    assert stats.objects >= 1


def test_api_store_stats_empty(tmp_path, monkeypatch):
    """store_stats on empty store returns zeros."""
    monkeypatch.chdir(tmp_path)
    stats = store_stats()
    assert stats.snapshots == 0
    assert stats.objects == 0


def test_api_store_gc(tmp_path, monkeypatch):
    """store_gc returns GCResult."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("hello")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="gc-test")

    result = store_gc()
    assert result.removed_objects >= 0
    assert result.freed_bytes >= 0
