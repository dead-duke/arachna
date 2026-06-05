"""Tests for public watch API (v2.0.0)."""

import json

import pytest

from arachna.api_errors import (
    ProfileNotFoundError,
    SnapshotExistsError,
    SnapshotNotFoundError,
)
from arachna.watch import (
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    snapshot_info,
    update_snapshot,
)


def _make_profile(directory: str, patterns=None) -> dict:
    return {
        "directories": [directory],
        "patterns": patterns or ["*"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


def _setup_config(tmp_path, monkeypatch, profiles=None):
    """Create a minimal .arachna.json and chdir to tmp_path."""
    monkeypatch.chdir(tmp_path)
    config = {"project_name": "test", "output_dir": "out", "profiles": profiles or {}}
    (tmp_path / ".arachna.json").write_text(json.dumps(config))
    return config


def test_api_create_snapshot(tmp_path, monkeypatch):
    """Programmatic snapshot creation returns ID."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile=profile, name="api-test")
    assert sid == "api-test"


def test_api_create_snapshot_duplicate(tmp_path, monkeypatch):
    """Duplicate snapshot name raises SnapshotExistsError."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")

    profile = _make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="dup-test")

    with pytest.raises(SnapshotExistsError):
        create_snapshot(profile=profile, name="dup-test")


def test_api_create_snapshot_profile_not_found(tmp_path, monkeypatch):
    """Non-existent profile name raises ProfileNotFoundError."""
    _setup_config(
        tmp_path, monkeypatch, profiles={"code": {"command": "echo hi", "max_tokens": 100}}
    )
    with pytest.raises(ProfileNotFoundError):
        create_snapshot(profile="nonexistent_profile_xyz", name="test")


def test_api_list_snapshots(tmp_path, monkeypatch):
    """list_snapshots returns list of SnapshotInfo."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")

    profile = _make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="s1")
    create_snapshot(profile=profile, name="s2")

    snaps = list_snapshots()
    assert len(snaps) == 2
    assert snaps[0].id == "s2"  # newest first
    assert isinstance(snaps[0].file_count, int)


def test_api_snapshot_info(tmp_path, monkeypatch):
    """snapshot_info returns SnapshotInfo with details."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")

    profile = _make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="info-test")

    info = snapshot_info("info-test")
    assert info.id == "info-test"
    assert info.file_count == 1


def test_api_snapshot_info_not_found(tmp_path, monkeypatch):
    """Non-existent snapshot raises SnapshotNotFoundError."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SnapshotNotFoundError):
        snapshot_info("nonexistent")


def test_api_delete_snapshot(tmp_path, monkeypatch):
    """delete_snapshot removes snapshot."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")

    profile = _make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="to-delete")
    delete_snapshot("to-delete")

    with pytest.raises(SnapshotNotFoundError):
        snapshot_info("to-delete")


def test_api_delete_snapshot_not_found(tmp_path, monkeypatch):
    """Deleting non-existent snapshot raises SnapshotNotFoundError."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SnapshotNotFoundError):
        delete_snapshot("nonexistent")


def test_api_update_snapshot(tmp_path, monkeypatch):
    """update_snapshot updates snapshot content."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = _make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="upd-test")

    (src / "a.py").write_text("modified")
    update_snapshot("upd-test", profile=profile)

    info = snapshot_info("upd-test")
    assert info.file_count == 1
