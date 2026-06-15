"""Extended integration tests for CLI coverage gaps."""

import json

from tests.integration.conftest import _arachna


def test_completion_bash():
    result = _arachna("completion", "bash")
    assert result.returncode == 0
    assert "complete -F _arachna_complete arachna" in result.stdout


def test_completion_zsh():
    result = _arachna("completion", "zsh")
    assert result.returncode == 0
    assert "#compdef arachna" in result.stdout


def test_validate_multi_profile(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "good": {"directories": ["src"], "max_tokens": 100, "split_mode": "by_file"},
                    "bad": {"max_tokens": 0},
                }
            }
        )
    )
    result = _arachna("collect", "--validate", cwd=tmp_path)
    assert result.returncode == 1
    assert "bad" in result.stdout


def test_init_interactive_cli(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / ".git").mkdir()
    result = _arachna("init", "--defaults", cwd=tmp_path)
    assert result.returncode == 0
    assert (tmp_path / ".arachna.json").exists()


def test_install_hook_force(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "hooks").mkdir()
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    result1 = _arachna("init", "--install-hook", cwd=tmp_path)
    assert result1.returncode == 0

    result2 = _arachna("init", "--install-hook", "--force", cwd=tmp_path)
    assert result2.returncode == 0

    hook = tmp_path / ".git" / "hooks" / "post-commit"
    assert hook.exists()
    assert "arachna collect --all" in hook.read_text()


def test_all_dry_run(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
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
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    },
                    "cmd": {
                        "command": "echo hi",
                        "max_tokens": 100,
                        "split_mode": "by_file",
                    },
                },
            }
        )
    )

    result = _arachna("collect", "--all", "--dry-run", cwd=tmp_path)
    assert result.returncode == 0
    assert "[code] section" in result.stdout
    assert "[cmd] section" in result.stdout

    if out_dir.exists():
        files = list(out_dir.glob("chat-*"))
        assert len(files) == 0


def test_format_json_all(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
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
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    result = _arachna("collect", "--all", "--format", "json", cwd=tmp_path)
    assert result.returncode == 0

    files = list(out_dir.glob("chat-code*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert '"path":' in content
    assert '"content":' in content


def test_merge_dry_run(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
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
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    result = _arachna("collect", "--profile", "code", "--merge", "--dry-run", cwd=tmp_path)
    assert result.returncode == 0
    assert "main.py" in result.stdout

    if out_dir.exists():
        files = list(out_dir.glob("chat-code*"))
        assert len(files) == 0
