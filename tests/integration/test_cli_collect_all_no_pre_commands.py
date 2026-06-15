import json

from tests.integration.conftest import _arachna


def test_collect_all_no_pre_commands(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
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
                        "pre_commands": ["echo 'SHOULD_NOT_APPEAR'"],
                    },
                    "cmd": {
                        "command": "echo 'cmd output'",
                        "max_tokens": 100,
                        "split_mode": "by_file",
                    },
                },
            }
        )
    )
    result = _arachna("collect", "--all", "--no-pre-commands", cwd=tmp_path)
    assert result.returncode == 0
    code_files = list(out_dir.glob("chat-code*"))
    assert len(code_files) >= 1
    content = code_files[0].read_text()
    assert "SHOULD_NOT_APPEAR" not in content
    assert "main.py" in content


def test_collect_all_dry_run_no_pre_commands(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
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
                        "pre_commands": ["echo 'SHOULD_NOT_APPEAR'"],
                    }
                },
            }
        )
    )
    result = _arachna("collect", "--all", "--dry-run", "--no-pre-commands", cwd=tmp_path)
    assert result.returncode == 0
    assert "SHOULD_NOT_APPEAR" not in result.stdout
    assert "main.py" in result.stdout
