"""Tests for v1.6.3 — Watch command-based profiles support."""

from arachna.store import load_snapshot
from arachna.watcher import compute_diff, create_snapshot


def _make_file_profile(directory: str, patterns=None, files=None) -> dict:
    """Helper to create a minimal file-based profile dict."""
    return {
        "directories": [directory],
        "patterns": patterns or ["*"],
        "files": files or [],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


def _make_command_profile(command: str) -> dict:
    """Helper to create a command-based profile dict."""
    return {
        "command": command,
        "split_mode": "by_paragraph",
        "max_tokens": 16000,
    }


def test_create_snapshot_with_pre_commands(tmp_path, monkeypatch):
    """create_snapshot stores pre_commands output in manifest."""
    monkeypatch.chdir(tmp_path)
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

    sid = create_snapshot(profile, name="with-pre-commands")
    manifest = load_snapshot(sid)

    assert "pre_commands" in manifest
    assert len(manifest["pre_commands"]) == 2
    assert any("echo" in key for key in manifest["pre_commands"])
    # Files still collected
    assert "files" in manifest
    assert len(manifest["files"]) == 1


def test_create_snapshot_with_command_profile(tmp_path, monkeypatch):
    """create_snapshot handles command-based profiles."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    profile = {
        "command": "echo 'command output'",
        "split_mode": "by_paragraph",
        "max_tokens": 16000,
    }

    sid = create_snapshot(profile, name="cmd-profile")
    manifest = load_snapshot(sid)

    assert "command" in manifest
    assert "command output" in manifest["command"]
    # No files — command-based profile
    assert manifest.get("files", {}) == {}


def test_compute_diff_command_changed(tmp_path, monkeypatch):
    """compute_diff detects changes in command output."""
    monkeypatch.chdir(tmp_path)

    profile = _make_command_profile("echo 'version 1'")
    sid = create_snapshot(profile, name="cmd-snap")

    # Change the command output
    profile2 = _make_command_profile("echo 'version 2'")
    diffs = compute_diff(sid, profile2)

    assert len(diffs) == 1
    assert diffs[0].type == "modified"
    assert "command output" in diffs[0].path
    assert "REMOVED" in diffs[0].content or "ADDED" in diffs[0].content


def test_compute_diff_pre_commands_changed(tmp_path, monkeypatch):
    """compute_diff detects changes in pre_commands output."""
    monkeypatch.chdir(tmp_path)
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
    sid = create_snapshot(profile, name="pre-snap")

    # Change pre_commands
    profile2 = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo 'after'"],
    }
    diffs = compute_diff(sid, profile2)

    # Should have at least one pre_commands diff
    pre_diffs = [d for d in diffs if d.path.startswith("pre:")]
    assert len(pre_diffs) >= 1
    assert pre_diffs[0].type in ("modified", "added", "deleted")


def test_compute_diff_command_unchanged(tmp_path, monkeypatch):
    """compute_diff produces no diff when command output is unchanged."""
    monkeypatch.chdir(tmp_path)

    profile = _make_command_profile("echo 'stable output'")
    sid = create_snapshot(profile, name="stable-snap")

    diffs = compute_diff(sid, profile)
    # Command output unchanged — no command-related diffs
    cmd_diffs = [d for d in diffs if "command output" in d.path]
    assert len(cmd_diffs) == 0


def test_manifest_backward_compatible(tmp_path, monkeypatch):
    """Old manifests without pre_commands/command fields are handled gracefully."""
    import json

    monkeypatch.chdir(tmp_path)

    # Manually create an old-format manifest (no pre_commands, no command)
    from arachna.store import _store_root, write_object

    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    test_hash = write_object(b"print('hello')")
    old_manifest = {
        "id": "old-snap",
        "name": "old-snap",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"src/main.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "old-snap.json").write_text(json.dumps(old_manifest))
    (store_dir / "HEAD").write_text("old-snap")

    # Now compute_diff with a profile that has pre_commands
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo 'new pre command'"],
    }

    diffs = compute_diff("old-snap", profile)
    # Should handle missing pre_commands gracefully — new pre_commands = added
    pre_diffs = [d for d in diffs if d.path.startswith("pre:")]
    assert len(pre_diffs) >= 1
    assert pre_diffs[0].type == "added"


def test_create_snapshot_empty_pre_commands_skipped(tmp_path, monkeypatch):
    """Empty pre_commands output is not stored in manifest."""
    monkeypatch.chdir(tmp_path)
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

    sid = create_snapshot(profile, name="empty-pre")
    manifest = load_snapshot(sid)

    # Empty output should be skipped
    assert "pre_commands" not in manifest or len(manifest["pre_commands"]) == 0


def test_compute_diff_command_added(tmp_path, monkeypatch):
    """compute_diff detects when a command is added to a profile that had none."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    # Snapshot without command
    profile_no_cmd = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }
    sid = create_snapshot(profile_no_cmd, name="no-cmd")

    # Now add command
    profile_with_cmd = {
        "command": "echo 'new command'",
        "split_mode": "by_paragraph",
        "max_tokens": 16000,
    }
    diffs = compute_diff(sid, profile_with_cmd)

    cmd_diffs = [d for d in diffs if d.path == "command output"]
    assert len(cmd_diffs) == 1
    assert cmd_diffs[0].type == "added"


def test_compute_diff_command_removed(tmp_path, monkeypatch):
    """compute_diff detects when a command is removed from a profile."""
    monkeypatch.chdir(tmp_path)

    profile_with_cmd = _make_command_profile("echo 'old command'")
    sid = create_snapshot(profile_with_cmd, name="with-cmd")

    # Remove command
    profile_no_cmd = {}
    diffs = compute_diff(sid, profile_no_cmd)

    cmd_diffs = [d for d in diffs if d.path == "command output"]
    assert len(cmd_diffs) == 1
    assert cmd_diffs[0].type == "deleted"
