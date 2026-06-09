import json
from unittest.mock import patch

from arachna.__main__ import main


def test_no_pre_commands_flag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
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
                        "pre_commands": ["echo 'TREE OUTPUT'"],
                    }
                },
            }
        )
    )

    with patch("sys.argv", ["arachna", "collect", "--profile", "code", "--no-pre-commands"]):
        main()

    out_dir = tmp_path / "out"
    files = list(out_dir.glob("chat-code*"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "main.py" in content
    assert "TREE OUTPUT" not in content


def test_no_pre_commands_without_flag_shows_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
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
                        "pre_commands": ["echo 'TREE OUTPUT'"],
                    }
                },
            }
        )
    )

    with patch("sys.argv", ["arachna", "collect", "--profile", "code"]):
        main()

    out_dir = tmp_path / "out"
    files = list(out_dir.glob("chat-code*"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "TREE OUTPUT" in content
