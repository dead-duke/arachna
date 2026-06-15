"""Tests for v1.6.3 - Watch command-based profiles support."""

import json

from arachna.store import load_snapshot
from arachna.watcher import compute_diff, create_snapshot


def test_create_snapshot_with_pre_commands(tmp_path, setup_config):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo '=== TREE ==='", "echo 'another command'"],
    }

    sid = create_snapshot(profile, name="with-pre-commands", root=root)
    manifest = load_snapshot(sid, root=root)

    assert "pre_commands" in manifest
    assert len(manifest["pre_commands"]) == 2
    assert any("echo" in key for key in manifest["pre_commands"])
    assert "files" in manifest
    assert len(manifest["files"]) == 1


def test_create_snapshot_with_command_profile(tmp_path, setup_config):
    root = setup_config()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    profile = {
        "command": "echo 'command output'",
        "split_mode": "by_paragraph",
        "max_tokens": 16000,
    }

    sid = create_snapshot(profile, name="cmd-profile", root=root)
    manifest = load_snapshot(sid, root=root)

    assert "command" in manifest
    assert "command output" in manifest["command"]
    assert manifest.get("files", {}) == {}


def test_compute_diff_command_changed(tmp_path, setup_config):
    root = setup_config()

    profile = {
        "command": "echo 'version 1'",
        "split_mode": "by_paragraph",
        "max_tokens": 16000,
    }
    sid = create_snapshot(profile, name="cmd-snap", root=root)

    profile2 = {
        "command": "echo 'version 2'",
        "split_mode": "by_paragraph",
        "max_tokens": 16000,
    }
    diffs = compute_diff(sid, profile2, root=root)

    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1
    assert content_diffs[0].type == "modified"
    assert "command output" in content_diffs[0].path


def test_compute_diff_pre_commands_changed(tmp_path, setup_config):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo 'before'"],
    }
    sid = create_snapshot(profile, name="pre-snap", root=root)

    profile2 = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo 'after'"],
    }
    diffs = compute_diff(sid, profile2, root=root)

    pre_diffs = [d for d in diffs if d.path and d.path.startswith("pre:")]
    assert len(pre_diffs) >= 1
    assert pre_diffs[0].type in ("modified", "added", "deleted")


def test_compute_diff_command_unchanged(tmp_path, setup_config):
    root = setup_config()

    profile = {
        "command": "echo 'stable output'",
        "split_mode": "by_paragraph",
        "max_tokens": 16000,
    }
    sid = create_snapshot(profile, name="stable-snap", root=root)

    diffs = compute_diff(sid, profile, root=root)
    cmd_diffs = [d for d in diffs if d.path and "command output" in d.path]
    assert len(cmd_diffs) == 0


def test_manifest_backward_compatible(tmp_path, setup_config):
    root = setup_config()
    from arachna.store import _store_root, write_object

    store_dir = _store_root(root=root)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    test_hash = write_object(b"print('hello')", root=root)
    old_manifest = {
        "id": "old-snap",
        "name": "old-snap",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"src/main.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "old-snap.json").write_text(json.dumps(old_manifest))
    (store_dir / "HEAD").write_text("old-snap")

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo 'new pre command'"],
    }

    diffs = compute_diff("old-snap", profile, root=root)
    pre_diffs = [d for d in diffs if d.path and d.path.startswith("pre:")]
    assert len(pre_diffs) >= 1
    assert pre_diffs[0].type == "added"


def test_create_snapshot_empty_pre_commands_skipped(tmp_path, setup_config):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo ''", "echo -n ''"],
    }

    sid = create_snapshot(profile, name="empty-pre", root=root)
    manifest = load_snapshot(sid, root=root)

    assert "pre_commands" not in manifest or len(manifest["pre_commands"]) == 0


def test_compute_diff_command_added(tmp_path, setup_config):
    root = setup_config()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    profile_no_cmd = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }
    sid = create_snapshot(profile_no_cmd, name="no-cmd", root=root)

    profile_with_cmd = {
        "command": "echo 'new command'",
        "split_mode": "by_paragraph",
        "max_tokens": 16000,
    }
    diffs = compute_diff(sid, profile_with_cmd, root=root)

    cmd_diffs = [d for d in diffs if d.path == "command output"]
    assert len(cmd_diffs) == 1
    assert cmd_diffs[0].type == "added"


def test_compute_diff_command_removed(tmp_path, setup_config):
    root = setup_config()

    profile_with_cmd = {
        "command": "echo 'old command'",
        "split_mode": "by_paragraph",
        "max_tokens": 16000,
    }
    sid = create_snapshot(profile_with_cmd, name="with-cmd", root=root)

    profile_no_cmd = {}
    diffs = compute_diff(sid, profile_no_cmd, root=root)

    cmd_diffs = [d for d in diffs if d.path == "command output"]
    assert len(cmd_diffs) == 1
    assert cmd_diffs[0].type == "deleted"
