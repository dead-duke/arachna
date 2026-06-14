"""Tests for update_snapshot and _collect_snapshot_content in watcher.py (v1.6.4)."""

import json

import pytest

from arachna.store import load_snapshot
from arachna.watcher import _collect_snapshot_content, create_snapshot, update_snapshot


def test_collect_snapshot_content_files(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "utils.py").write_text("x = 1")

    profile = make_profile("src", ["*.py"])
    files, pre, cmd = _collect_snapshot_content(profile)

    assert len(files) == 2
    assert any("main.py" in f for f in files)
    assert any("utils.py" in f for f in files)
    assert pre == {}
    assert cmd == {}


def test_collect_snapshot_content_with_pre_commands(tmp_path, setup_config):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo 'hello world'"],
    }
    files, pre, cmd = _collect_snapshot_content(profile)

    assert len(files) == 1
    assert len(pre) == 1
    assert any("sha256:" in v for v in pre.values())
    assert cmd == {}


def test_collect_snapshot_content_with_command(tmp_path, setup_config):
    setup_config()

    profile = {
        "command": "echo 'command output'",
        "split_mode": "by_paragraph",
        "max_tokens": 16000,
    }
    files, pre, cmd = _collect_snapshot_content(profile)

    assert files == {}
    assert pre == {}
    assert len(cmd) == 1
    assert "command output" in cmd
    assert cmd["command output"].startswith("sha256:")


def test_collect_snapshot_content_empty_pre_commands(tmp_path, setup_config):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo -n ''"],
    }
    files, pre, cmd = _collect_snapshot_content(profile)

    assert len(files) == 1
    assert pre == {}


def test_watcher_update_snapshot_replaces_files(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("first")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile, name="w-update")

    (src / "a.py").write_text("second")
    (src / "b.py").write_text("new file")

    update_snapshot("w-update", profile)

    manifest = load_snapshot("w-update")
    assert len(manifest["files"]) == 2
    assert any("a.py" in f for f in manifest["files"])
    assert any("b.py" in f for f in manifest["files"])


def test_watcher_update_snapshot_uses_existing_profile(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")

    profile = make_profile("src", ["*.py"])
    create_snapshot(profile, name="w-auto-profile")

    (src / "b.py").write_text("new")

    update_snapshot("w-auto-profile")

    manifest = load_snapshot("w-auto-profile")
    assert len(manifest["files"]) == 2


def test_watcher_update_snapshot_legacy_profile_raises(tmp_path, setup_config):
    setup_config()
    from arachna.store import _store_root, write_object

    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    test_hash = write_object(b"legacy content")
    old_manifest = {
        "id": "legacy-snap",
        "name": "legacy-snap",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"src/main.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "legacy-snap.json").write_text(json.dumps(old_manifest))

    with pytest.raises(ValueError, match="legacy format"):
        update_snapshot("legacy-snap")
