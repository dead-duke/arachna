import pytest

from arachna.api.api_errors import SnapshotNotFoundError
from arachna.api.snapshot import (
    compute_diff,
    create_snapshot,
    snapshot_info,
    store_gc,
    store_stats,
    update_snapshot,
)
from arachna.config.core.config import get_profile, load_config
from arachna.config.profile_config import ProfileConfig


def _resolve(tmp_path, profile):
    if isinstance(profile, ProfileConfig):
        return profile, load_config(root=tmp_path)
    config = load_config(root=tmp_path)
    return get_profile(profile, root=tmp_path, config=config), config


def test_api_compute_diff_modified(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="diff-snap")
    (src / "a.py").write_text("modified")
    result = compute_diff(root=root, snapshot_id="diff-snap", profile=profile, config=config)
    assert result.stats.modified >= 1
    assert any(s.type == "modified" for s in result.sections if s.path)


def test_api_compute_diff_no_changes(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("same")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="no-changes")
    result = compute_diff(root=root, snapshot_id="no-changes", profile=profile, config=config)
    assert result.stats.modified == 0


def test_api_compute_diff_auto_select(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="auto-snap")
    result = compute_diff(root=root, profile=profile, config=config)
    assert result.snapshot_id == "auto-snap"


def test_api_compute_diff_no_snapshots(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    with pytest.raises(SnapshotNotFoundError):
        compute_diff(root=root, profile=profile, config=config)


def test_api_compute_diff_multiple_snapshots_raises(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="s1")
    create_snapshot(root=root, profile=profile, config=config, name="s2")
    with pytest.raises(ValueError):
        compute_diff(root=root, profile=profile, config=config)


def test_api_compute_diff_cross_snapshot(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("v1")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="v1")
    (src / "a.py").write_text("v2")
    create_snapshot(root=root, profile=profile, config=config, name="v2")
    result = compute_diff(
        root=root, snapshot_id="v1", profile=profile, config=config, to_snapshot_id="v2"
    )
    assert result.stats.modified >= 1


def test_api_compute_diff_structural_mode(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("def foo():\n    return 1\n")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="struct-snap")
    (src / "a.py").write_text("def foo():\n    return 2\n")
    result = compute_diff(
        root=root, snapshot_id="struct-snap", profile=profile, config=config, mode="structural"
    )
    assert result.stats.modified >= 1


def test_api_compute_diff_repo_map_mode(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("def foo():\n    return 1\n\ndef bar():\n    return 2\n")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="rm-snap")
    (src / "a.py").write_text("def foo():\n    return 3\n\ndef bar():\n    return 4\n")
    result = compute_diff(
        root=root, snapshot_id="rm-snap", profile=profile, config=config, mode="repo-map"
    )
    assert result.stats.modified >= 1


def test_api_compute_diff_profile_not_found(tmp_path, setup_config):
    root = setup_config(profiles={"x": {"command": "echo hi", "max_tokens": 100}})
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x")
    config = load_config(root=root)
    with pytest.raises(KeyError):
        get_profile("nonexistent", root=root, config=config)


def test_api_update_snapshot_profile_dict(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="api-upd")
    (src / "a.py").write_text("modified")
    update_snapshot("api-upd", root=root, profile=profile, config=config)
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
    config = load_config(root=root)
    profile = get_profile("code", root=root, config=config)
    create_snapshot(root=root, profile=profile, config=config, name="api-upd2")
    (src / "a.py").write_text("modified")
    update_snapshot("api-upd2", root=root, profile=profile, config=config)


def test_api_update_snapshot_not_found(tmp_path, setup_config, make_profile):
    root = setup_config()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    with pytest.raises(SnapshotNotFoundError):
        update_snapshot("nonexistent", root=root, profile=profile, config=config)


def test_api_store_stats(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("hello")
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="stats-test")
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
    profile, config = _resolve(tmp_path, make_profile("src", ["*.py"]))
    create_snapshot(root=root, profile=profile, config=config, name="gc-test")
    result = store_gc(root=root)
    assert result.removed_objects >= 0
    assert result.freed_bytes >= 0
