"""Tests for public watch API (v2.0.0)."""

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


def test_api_create_snapshot(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile=profile, name="api-test")
    assert sid == "api-test"


def test_api_create_snapshot_duplicate(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="dup-test")

    with pytest.raises(SnapshotExistsError):
        create_snapshot(profile=profile, name="dup-test")


def test_api_create_snapshot_profile_not_found(tmp_path, setup_config):
    setup_config(profiles={"code": {"command": "echo hi", "max_tokens": 100}})
    with pytest.raises(ProfileNotFoundError):
        create_snapshot(profile="nonexistent_profile_xyz", name="test")


def test_api_list_snapshots(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="s1")
    create_snapshot(profile=profile, name="s2")

    snaps = list_snapshots()
    assert len(snaps) == 2
    assert snaps[0].id == "s2"  # newest first
    assert isinstance(snaps[0].file_count, int)


def test_api_snapshot_info(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="info-test")

    info = snapshot_info("info-test")
    assert info.id == "info-test"
    assert info.file_count == 1


def test_api_snapshot_info_not_found(tmp_path, setup_config):
    setup_config()
    with pytest.raises(SnapshotNotFoundError):
        snapshot_info("nonexistent")


def test_api_delete_snapshot(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="to-delete")
    delete_snapshot("to-delete")

    with pytest.raises(SnapshotNotFoundError):
        snapshot_info("to-delete")


def test_api_delete_snapshot_not_found(tmp_path, setup_config):
    setup_config()
    with pytest.raises(SnapshotNotFoundError):
        delete_snapshot("nonexistent")


def test_api_update_snapshot(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="upd-test")

    (src / "a.py").write_text("modified")
    update_snapshot("upd-test", profile=profile)

    info = snapshot_info("upd-test")
    assert info.file_count == 1
