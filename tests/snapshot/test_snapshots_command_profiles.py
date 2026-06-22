import json

from arachna.config.profile_config import ProfileConfig
from arachna.snapshot.diff.snapshot_diff import compute_diff, create_snapshot
from arachna.snapshot.store import load_snapshot


def _file_profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
        exclude_patterns=[],
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def _cmd_profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_paragraph",
        command="echo 'command output'",
        directories=[],
        patterns=[],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_create_snapshot_with_pre_commands(tmp_path, setup_config):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    p = _file_profile(pre_commands=["echo '=== TREE ==='", "echo 'another command'"])
    sid = create_snapshot(p, name="with-pre-commands", root=root)
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

    sid = create_snapshot(_cmd_profile(), name="cmd-profile", root=root)
    manifest = load_snapshot(sid, root=root)

    assert "command" in manifest
    assert "command output" in manifest["command"]
    assert manifest.get("files", {}) == {}


def test_compute_diff_command_changed(tmp_path, setup_config):
    root = setup_config()
    sid = create_snapshot(_cmd_profile(command="echo 'version 1'"), name="cmd-snap", root=root)
    diffs = compute_diff(sid, _cmd_profile(command="echo 'version 2'"), root=root)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1
    assert content_diffs[0].type == "modified"
    assert "command output" in content_diffs[0].path


def test_compute_diff_pre_commands_changed(tmp_path, setup_config):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    p1 = _file_profile(pre_commands=["echo 'before'"])
    sid = create_snapshot(p1, name="pre-snap", root=root)

    p2 = _file_profile(pre_commands=["echo 'after'"])
    diffs = compute_diff(sid, p2, root=root)

    pre_diffs = [d for d in diffs if d.path and d.path.startswith("pre:")]
    assert len(pre_diffs) >= 1
    assert pre_diffs[0].type in ("modified", "added", "deleted")


def test_compute_diff_command_unchanged(tmp_path, setup_config):
    root = setup_config()
    p = _cmd_profile(command="echo 'stable output'")
    sid = create_snapshot(p, name="stable-snap", root=root)
    diffs = compute_diff(sid, p, root=root)
    cmd_diffs = [d for d in diffs if d.path and "command output" in d.path]
    assert len(cmd_diffs) == 0


def test_manifest_backward_compatible(tmp_path, setup_config):
    root = setup_config()
    from arachna.snapshot.store import _store_root, write_object

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

    p = _file_profile(pre_commands=["echo 'new pre command'"])
    diffs = compute_diff("old-snap", p, root=root)
    pre_diffs = [d for d in diffs if d.path and d.path.startswith("pre:")]
    assert len(pre_diffs) >= 1
    assert pre_diffs[0].type == "added"


def test_create_snapshot_empty_pre_commands_skipped(tmp_path, setup_config):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    p = _file_profile(pre_commands=["echo ''", "echo -n ''"])
    sid = create_snapshot(p, name="empty-pre", root=root)
    manifest = load_snapshot(sid, root=root)
    assert "pre_commands" not in manifest or len(manifest["pre_commands"]) == 0


def test_compute_diff_command_added(tmp_path, setup_config):
    root = setup_config()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    p_no_cmd = _file_profile()
    sid = create_snapshot(p_no_cmd, name="no-cmd", root=root)

    p_with_cmd = _cmd_profile(command="echo 'new command'")
    diffs = compute_diff(sid, p_with_cmd, root=root)

    cmd_diffs = [d for d in diffs if d.path == "command output"]
    assert len(cmd_diffs) == 1
    assert cmd_diffs[0].type == "added"


def test_compute_diff_command_removed(tmp_path, setup_config):
    root = setup_config()
    p_with_cmd = _cmd_profile(command="echo 'old command'")
    sid = create_snapshot(p_with_cmd, name="with-cmd", root=root)

    p_no_cmd = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[],
        patterns=[],
        use_gitignore=False,
    )
    diffs = compute_diff(sid, p_no_cmd, root=root)

    cmd_diffs = [d for d in diffs if d.path == "command output"]
    assert len(cmd_diffs) == 1
    assert cmd_diffs[0].type == "deleted"
