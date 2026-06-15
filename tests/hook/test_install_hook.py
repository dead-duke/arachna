import json
import stat
import sys

from arachna.hook import install_hook


def test_install_hook_default_command(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    success, msg = install_hook(root=tmp_path)
    assert success
    hook = git_dir / "hooks" / "post-commit"
    assert hook.exists()
    content = hook.read_text()
    assert "arachna collect --all" in content
    if sys.platform != "win32":
        assert hook.stat().st_mode & stat.S_IXUSR


def test_install_hook_custom_command_from_config(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {"project_name": "test", "hook": {"post-commit": "arachna collect --all --incremental"}}
        )
    )

    success, msg = install_hook(root=tmp_path)
    assert success
    content = (git_dir / "hooks" / "post-commit").read_text()
    assert "arachna collect --all --incremental" in content


def test_install_hook_explicit_command(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "hook": {"post-commit": "arachna collect --all"}})
    )

    success, msg = install_hook(command="arachna collect --profile code", root=tmp_path)
    assert success
    content = (git_dir / "hooks" / "post-commit").read_text()
    assert "arachna collect --profile code" in content


def test_install_hook_not_git_repo(tmp_path):
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    success, msg = install_hook(root=tmp_path)
    assert not success
    assert "Not a git repository" in msg


def test_install_hook_no_config(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()

    success, msg = install_hook(root=tmp_path)
    assert success
    content = (git_dir / "hooks" / "post-commit").read_text()
    assert "arachna collect --all" in content


def test_install_hook_existing_refuses(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))
    hook = git_dir / "hooks" / "post-commit"
    hook.write_text("#!/bin/sh\necho old")

    success, msg = install_hook(root=tmp_path)
    assert not success
    assert "already exists" in msg
    assert "echo old" in hook.read_text()


def test_install_hook_existing_force_overwrites(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))
    hook = git_dir / "hooks" / "post-commit"
    hook.write_text("#!/bin/sh\necho old")

    success, msg = install_hook(force=True, root=tmp_path)
    assert success
    content = hook.read_text()
    assert "arachna collect --all" in content
    assert "echo old" not in content


def test_install_hook_creates_hooks_dir(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    success, msg = install_hook(root=tmp_path)
    assert success
    assert (git_dir / "hooks" / "post-commit").exists()
