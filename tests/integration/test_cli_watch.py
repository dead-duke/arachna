"""Integration tests for Watch CLI — snapshot, diff, store."""

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


# TC-053: --snapshot creates snapshot and lists it
def test_snapshot_create_and_list(tmp_path, monkeypatch):
    """TC-053: --snapshot creates a snapshot, --snapshot list shows it."""
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
                    }
                },
            }
        )
    )

    result = _arachna("--snapshot", "--profile", "code", "--name", "list-test")
    assert result.returncode == 0

    result = _arachna("--snapshot")
    assert result.returncode == 0
    assert "list-test" in result.stdout
    assert "1 files" in result.stdout


# TC-054: --snapshot --name creates named snapshot
def test_snapshot_named(tmp_path, monkeypatch):
    """TC-054: --snapshot --name creates snapshot with given name."""
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
                    }
                },
            }
        )
    )

    result = _arachna("--snapshot", "--profile", "code", "--name", "my-snap")
    assert result.returncode == 0
    assert "my-snap" in result.stdout

    result = _arachna("--snapshot")
    assert "my-snap" in result.stdout


# TC-055: --snapshot delete removes snapshot
def test_snapshot_delete(tmp_path, monkeypatch):
    """TC-055: --snapshot delete removes a snapshot."""
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
                    }
                },
            }
        )
    )

    _arachna("--snapshot", "--profile", "code", "--name", "to-delete")
    result = _arachna("--snapshot", "delete", "to-delete")
    assert result.returncode == 0

    result = _arachna("--snapshot")
    assert "to-delete" not in result.stdout


# TC-056: --snapshot delete non-existent exits 1
def test_snapshot_delete_not_found(tmp_path, monkeypatch):
    """TC-056: --snapshot delete for non-existent snapshot exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    result = _arachna("--snapshot", "delete", "nonexistent")
    assert result.returncode == 1


# TC-057: --diff detects modified file
def test_diff_modified(tmp_path, monkeypatch):
    """TC-057: --diff detects files modified since snapshot."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
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

    _arachna("--snapshot", "--profile", "code", "--name", "snap1")
    (tmp_path / "src" / "main.py").write_text("modified")

    result = _arachna("--diff", "--from", "snap1", "--profile", "code")
    assert result.returncode == 0
    assert "REMOVED" in result.stdout or "ADDED" in result.stdout


# TC-058: --diff with no snapshot exits 1
def test_diff_no_snapshot(tmp_path, monkeypatch):
    """TC-058: --diff without snapshots exits 1."""
    monkeypatch.chdir(tmp_path)
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

    result = _arachna("--diff", "--profile", "code")
    assert result.returncode == 1


# TC-059: --store stats shows statistics
def test_store_stats(tmp_path, monkeypatch):
    """TC-059: --store stats shows store statistics."""
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
                    }
                },
            }
        )
    )

    _arachna("--snapshot", "--profile", "code")

    result = _arachna("--store", "stats")
    assert result.returncode == 0
    assert "Snapshots:" in result.stdout
    assert "Objects:" in result.stdout


# TC-060: --store gc garbage collects
def test_store_gc(tmp_path, monkeypatch):
    """TC-060: --store gc removes unreferenced objects."""
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
                    }
                },
            }
        )
    )

    _arachna("--snapshot", "--profile", "code")

    result = _arachna("--store", "gc")
    assert result.returncode == 0
