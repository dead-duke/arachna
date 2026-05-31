import json
import stat
import sys

from arachna.hook import install_hook


def test_install_hook_default_command(tmp_path, monkeypatch):
    """Happy path: install hook with default command."""
    monkeypatch.chdir(tmp_path)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    success, msg = install_hook()
    assert success
    hook = git_dir / "hooks" / "post-commit"
    assert hook.exists()
    content = hook.read_text()
    assert "arachna --all" in content
    # Check executable on Unix (Windows does not support this)
    if sys.platform != "win32":
        assert hook.stat().st_mode & stat.S_IXUSR


def test_install_hook_custom_command_from_config(tmp_path, monkeypatch):
    """Hook reads command from .arachna.json hook.post-commit."""
    monkeypatch.chdir(tmp_path)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "hook": {"post-commit": "arachna --all --incremental"},
            }
        )
    )

    success, msg = install_hook()
    assert success
    content = (git_dir / "hooks" / "post-commit").read_text()
    assert "arachna --all --incremental" in content


def test_install_hook_explicit_command(tmp_path, monkeypatch):
    """Explicit command parameter takes precedence over config."""
    monkeypatch.chdir(tmp_path)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "hook": {"post-commit": "arachna --all"},
            }
        )
    )

    success, msg = install_hook(command="arachna --profile code")
    assert success
    content = (git_dir / "hooks" / "post-commit").read_text()
    assert "arachna --profile code" in content


def test_install_hook_not_git_repo(tmp_path, monkeypatch):
    """Fails when not in a git repository."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    success, msg = install_hook()
    assert not success
    assert "Not a git repository" in msg


def test_install_hook_no_config(tmp_path, monkeypatch):
    """Works with default command when no .arachna.json."""
    monkeypatch.chdir(tmp_path)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()

    success, msg = install_hook()
    assert success
    content = (git_dir / "hooks" / "post-commit").read_text()
    assert "arachna --all" in content


def test_install_hook_existing_refuses(tmp_path, monkeypatch):
    """Refuses to overwrite existing hook without --force."""
    monkeypatch.chdir(tmp_path)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))
    hook = git_dir / "hooks" / "post-commit"
    hook.write_text("#!/bin/sh\necho old")

    success, msg = install_hook()
    assert not success
    assert "already exists" in msg
    assert "echo old" in hook.read_text()


def test_install_hook_existing_force_overwrites(tmp_path, monkeypatch):
    """--force overwrites existing hook."""
    monkeypatch.chdir(tmp_path)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))
    hook = git_dir / "hooks" / "post-commit"
    hook.write_text("#!/bin/sh\necho old")

    success, msg = install_hook(force=True)
    assert success
    content = hook.read_text()
    assert "arachna --all" in content
    assert "echo old" not in content


def test_install_hook_creates_hooks_dir(tmp_path, monkeypatch):
    """Creates .git/hooks directory if it doesn't exist."""
    monkeypatch.chdir(tmp_path)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    success, msg = install_hook()
    assert success
    assert (git_dir / "hooks" / "post-commit").exists()
