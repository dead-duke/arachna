"""Integration tests for init dispatch edge cases."""

import json

from tests.integration.conftest import _arachna


def test_init_install_hook_no_git_repo(tmp_path):
    """init --install-hook without .git exits 1."""
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("init", "--install-hook", cwd=tmp_path)
    assert result.returncode == 1


def test_init_defaults_with_preset(tmp_path):
    """init --defaults --preset with specific preset."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".git").mkdir()
    result = _arachna("init", "--defaults", "--preset", "python", cwd=tmp_path)
    assert result.returncode == 0
    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "python" in data["profiles"]


def test_init_defaults_git_only(tmp_path):
    """init --defaults with only .git present creates git profile."""
    (tmp_path / ".git").mkdir()
    result = _arachna("init", "--defaults", cwd=tmp_path)
    assert result.returncode == 0
    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert "git" in data["profiles"]
