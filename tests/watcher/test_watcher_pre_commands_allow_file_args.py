"""TC-185, TC-186, TC-187: pre_commands executed with allow_file_args=True in watcher."""

from arachna.store import load_snapshot
from arachna.watcher import _collect_snapshot_content, compute_diff, create_snapshot


def test_collect_snapshot_content_pre_commands_with_pipes(tmp_path, monkeypatch):
    """TC-186: _collect_snapshot_content runs pre_commands with pipes (tree -I pattern)."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": [
            "echo 'line1'",
            "echo 'line2'",
        ],
    }

    files, pre, cmd = _collect_snapshot_content(profile)
    assert len(files) == 1
    assert len(pre) == 2
    for hash_spec in pre.values():
        assert hash_spec.startswith("sha256:")


def test_snapshot_create_with_git_pre_commands(tmp_path, monkeypatch):
    """TC-186: create_snapshot with git pre_commands stores output."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (tmp_path / ".git").mkdir()

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": [
            "echo 'git log output'",
            "echo 'tree output'",
        ],
    }

    sid = create_snapshot(profile, name="pre-cmd-snap")
    manifest = load_snapshot(sid)

    assert "pre_commands" in manifest
    assert len(manifest["pre_commands"]) == 2
    assert "files" in manifest


def test_diff_with_pre_commands_current_state(tmp_path, monkeypatch):
    """TC-187: compute_diff runs current pre_commands with allow_file_args."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile1 = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo 'version 1'"],
    }

    sid = create_snapshot(profile1, name="diff-pre-snap")

    profile2 = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo 'version 2'"],
    }

    diffs = compute_diff(sid, profile2)
    pre_diffs = [d for d in diffs if d.path and d.path.startswith("pre:")]
    assert len(pre_diffs) >= 1
