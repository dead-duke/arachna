"""Tests for public watch API (v2.0.0)."""

import pytest

from arachna.api.api_errors import (
    ProfileNotFoundError,
    SnapshotExistsError,
    SnapshotNotFoundError,
)
from arachna.api.watch import (
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    snapshot_info,
    update_snapshot,
)


def test_api_create_snapshot(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile=profile, name="api-test", root=root)
    assert sid == "api-test"


def test_api_create_snapshot_duplicate(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="dup-test", root=root)

    with pytest.raises(SnapshotExistsError):
        create_snapshot(profile=profile, name="dup-test", root=root)


def test_api_create_snapshot_profile_not_found(tmp_path, setup_config):
    root = setup_config(profiles={"code": {"command": "echo hi", "max_tokens": 100}})
    with pytest.raises(ProfileNotFoundError):
        create_snapshot(profile="nonexistent_profile_xyz", name="test", root=root)


def test_api_list_snapshots(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="s1", root=root)
    create_snapshot(profile=profile, name="s2", root=root)

    snaps = list_snapshots(root=root)
    assert len(snaps) == 2
    assert snaps[0].id == "s2"
    assert isinstance(snaps[0].file_count, int)


def test_api_snapshot_info(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="info-test", root=root)

    info = snapshot_info("info-test", root=root)
    assert info.id == "info-test"
    assert info.file_count == 1


def test_api_snapshot_info_not_found(tmp_path, setup_config):
    root = setup_config()
    with pytest.raises(SnapshotNotFoundError):
        snapshot_info("nonexistent", root=root)


def test_api_delete_snapshot(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="to-delete", root=root)
    delete_snapshot("to-delete", root=root)

    with pytest.raises(SnapshotNotFoundError):
        snapshot_info("to-delete", root=root)


def test_api_delete_snapshot_not_found(tmp_path, setup_config):
    root = setup_config()
    with pytest.raises(SnapshotNotFoundError):
        delete_snapshot("nonexistent", root=root)


def test_api_update_snapshot(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile=profile, name="upd-test", root=root)

    (src / "a.py").write_text("modified")
    update_snapshot("upd-test", profile=profile, root=root)

    info = snapshot_info("upd-test", root=root)
    assert info.file_count == 1
