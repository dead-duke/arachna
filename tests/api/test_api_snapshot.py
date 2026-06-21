import json

import pytest

from arachna.api.api_errors import SnapshotExistsError, SnapshotNotFoundError
from arachna.api.snapshot import (
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    snapshot_info,
    update_snapshot,
)
from arachna.config.core.config import get_profile, load_config
from arachna.config.profile_config import ProfileConfig


def _resolve(tmp_path, profile):
    if isinstance(profile, ProfileConfig):
        return profile, load_config(root=tmp_path)
    config = load_config(root=tmp_path)
    return get_profile(profile, root=tmp_path, config=config), config


def test_api_create_snapshot(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    sid = create_snapshot(profile=profile, config=config, name="api-test", root=root)
    assert sid == "api-test"


def test_api_create_snapshot_name_required(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    with pytest.raises(ValueError, match="name is required"):
        create_snapshot(profile=profile, config=config, name=None, root=root)


def test_api_create_snapshot_duplicate(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(profile=profile, config=config, name="dup-test", root=root)
    with pytest.raises(SnapshotExistsError):
        create_snapshot(profile=profile, config=config, name="dup-test", root=root)


def test_api_create_snapshot_profile_not_found(tmp_path, setup_config):
    root = setup_config(profiles={"code": {"command": "echo hi", "max_tokens": 100}})
    config = load_config(root=root)
    with pytest.raises(KeyError):
        get_profile("nonexistent_profile_xyz", root=root, config=config)


def test_api_list_snapshots(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(profile=profile, config=config, name="s1", root=root)
    create_snapshot(profile=profile, config=config, name="s2", root=root)
    snaps = list_snapshots(root=root)
    assert len(snaps) == 2
    assert snaps[0].id == "s2"
    assert isinstance(snaps[0].file_count, int)


def test_api_snapshot_info(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(profile=profile, config=config, name="info-test", root=root)
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
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(profile=profile, config=config, name="to-delete", root=root)
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
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(profile=profile, config=config, name="upd-test", root=root)
    (src / "a.py").write_text("modified")
    update_snapshot("upd-test", profile=profile, config=config, root=root)
    info = snapshot_info("upd-test", root=root)
    assert info.file_count == 1


def test_api_update_snapshot_without_profile(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(profile=profile, config=config, name="upd-no-prof", root=root)
    (src / "a.py").write_text("modified")
    update_snapshot("upd-no-prof", root=root, config=config, profile=None)
    info = snapshot_info("upd-no-prof", root=root)
    assert info.file_count == 1


def test_api_update_snapshot_not_found(tmp_path, setup_config):
    root = setup_config()
    config = load_config(root=root)
    with pytest.raises(SnapshotNotFoundError):
        update_snapshot("nonexistent", root=root, config=config)


def test_api_update_snapshot_legacy_profile(tmp_path, setup_config):
    root = setup_config()
    from arachna.snapshot.store import _store_root, write_object

    store_dir = _store_root(root=root)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    test_hash = write_object(b"legacy content", root=root)
    old_manifest = {
        "id": "legacy-snap",
        "name": "legacy-snap",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"src/main.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "legacy-snap.json").write_text(json.dumps(old_manifest))
    config = load_config(root=root)
    with pytest.raises(ValueError, match="legacy format"):
        update_snapshot("legacy-snap", root=root, config=config, profile=None)
