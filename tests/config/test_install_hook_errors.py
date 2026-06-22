"""Tests for install_hook — corrupted config, missing fields."""

import json

from arachna.config.setup.hook import install_hook


def test_install_hook_corrupted_json_config(tmp_path):
    """Corrupted .arachna.json — falls back to default command."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text("not valid json")
    success, msg = install_hook(root=tmp_path)
    assert success
    content = (git_dir / "hooks" / "post-commit").read_text()
    assert "arachna collect --all" in content


def test_install_hook_no_hook_key_in_config(tmp_path):
    """Config without 'hook' key — falls back to default."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))
    success, msg = install_hook(root=tmp_path)
    assert success
    content = (git_dir / "hooks" / "post-commit").read_text()
    assert "arachna collect --all" in content
