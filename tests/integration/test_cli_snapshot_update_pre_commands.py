import json

from tests.integration.conftest import _arachna


def test_snapshot_update_pre_commands_not_blocked(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (tmp_path / ".git").mkdir()
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
                        "pre_commands": ["echo 'tree output'", "echo 'git log'"],
                    }
                },
            }
        )
    )
    r1 = _arachna("snapshot", "create", "--profile", "code", "--name", "pre-upd-snap", cwd=tmp_path)
    assert r1.returncode == 0
    assert "blocked" not in r1.stderr.lower()
    assert "blocked" not in r1.stdout.lower()
    (src / "main.py").write_text("print('updated')")
    r2 = _arachna("snapshot", "update", "pre-upd-snap", "--profile", "code", cwd=tmp_path)
    assert r2.returncode == 0
    assert "blocked" not in r2.stderr.lower()
    assert "blocked" not in r2.stdout.lower()


def test_diff_with_pre_commands_not_blocked(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (tmp_path / ".git").mkdir()
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
                        "pre_commands": ["echo 'tree output'"],
                    }
                },
            }
        )
    )
    r1 = _arachna(
        "snapshot", "create", "--profile", "code", "--name", "diff-pre-snap", cwd=tmp_path
    )
    assert r1.returncode == 0
    (src / "main.py").write_text("print('modified')")
    r2 = _arachna("diff", "--from", "diff-pre-snap", "--profile", "code", cwd=tmp_path)
    assert r2.returncode == 0
    assert "blocked" not in r2.stderr.lower()
    assert "blocked" not in r2.stdout.lower()
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
