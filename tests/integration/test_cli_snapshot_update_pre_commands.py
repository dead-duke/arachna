"""Integration tests for snapshot update with pre_commands. Updated for v3.0 CLI."""

import json
import os
import subprocess
import sys


def _arachna(*args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "arachna", *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def test_snapshot_update_pre_commands_not_blocked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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
                        "pre_commands": [
                            "echo 'tree output'",
                            "echo 'git log'",
                        ],
                    }
                },
            }
        )
    )

    r1 = _arachna("snapshot", "create", "--profile", "code", "--name", "pre-upd-snap")
    assert r1.returncode == 0
    assert "blocked" not in r1.stderr.lower()
    assert "blocked" not in r1.stdout.lower()

    (src / "main.py").write_text("print('updated')")
    r2 = _arachna("snapshot", "update", "pre-upd-snap", "--profile", "code")
    assert r2.returncode == 0
    assert "blocked" not in r2.stderr.lower()
    assert "blocked" not in r2.stdout.lower()


def test_diff_with_pre_commands_not_blocked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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
                        "pre_commands": [
                            "echo 'tree output'",
                        ],
                    }
                },
            }
        )
    )

    r1 = _arachna("snapshot", "create", "--profile", "code", "--name", "diff-pre-snap")
    assert r1.returncode == 0

    (src / "main.py").write_text("print('modified')")
    r2 = _arachna("diff", "--from", "diff-pre-snap", "--profile", "code")
    assert r2.returncode == 0
    assert "blocked" not in r2.stderr.lower()
    assert "blocked" not in r2.stdout.lower()

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
