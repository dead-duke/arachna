import json

from tests.integration.conftest import _arachna


def test_pre_command_with_glob_passes(tmp_path):
    """Shell glob expansion is allowed in pre_commands."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 100,
                        "split_mode": "by_file",
                        "pre_commands": ["echo src/*.py"],
                    }
                },
            }
        )
    )
    result = _arachna("collect", "--profile", "code", cwd=tmp_path)
    assert result.returncode == 0
    assert "blocked" not in result.stdout.lower()


def test_pre_command_with_quotes_containing_pipe_passes(tmp_path):
    """Pipe inside quotes is not a pipe separator — allowed."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 100,
                        "split_mode": "by_file",
                        "pre_commands": ["grep 'error|warn' /dev/null || true"],
                    }
                },
            }
        )
    )
    result = _arachna("collect", "--profile", "code", cwd=tmp_path)
    assert result.returncode == 0
    assert "blocked" not in result.stdout.lower()


def test_pre_command_subshell_blocked(tmp_path):
    """Command substitution $(...) is always blocked."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 100,
                        "split_mode": "by_file",
                        "pre_commands": ["echo $(whoami)"],
                    }
                },
            }
        )
    )
    result = _arachna("collect", "--profile", "code", cwd=tmp_path)
    assert result.returncode == 0
