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


# TC-053: --snapshot create and list
def test_snapshot_create_and_list(tmp_path, monkeypatch):
    """TC-053: --snapshot create creates, --snapshot list shows it."""
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

    result = _arachna("--snapshot", "create", "--profile", "code", "--name", "list-test")
    assert result.returncode == 0

    result = _arachna("--snapshot", "list")
    assert result.returncode == 0
    assert "list-test" in result.stdout


# TC-054: --snapshot create --name
def test_snapshot_named(tmp_path, monkeypatch):
    """TC-054: --snapshot create --name creates named snapshot."""
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

    result = _arachna("--snapshot", "create", "--profile", "code", "--name", "my-snap")
    assert result.returncode == 0
    assert "my-snap" in result.stdout

    result = _arachna("--snapshot", "list")
    assert "my-snap" in result.stdout


# TC-055: --snapshot delete
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

    _arachna("--snapshot", "create", "--profile", "code", "--name", "to-delete")
    result = _arachna("--snapshot", "delete", "to-delete")
    assert result.returncode == 0

    result = _arachna("--snapshot", "list")
    assert "to-delete" not in result.stdout


# TC-056: --snapshot delete non-existent
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

    _arachna("--snapshot", "create", "--profile", "code", "--name", "snap1")
    (tmp_path / "src" / "main.py").write_text("modified")

    result = _arachna("--diff", "--from", "snap1", "--profile", "code")
    assert result.returncode == 0

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "REMOVED" in content or "ADDED" in content


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


# TC-059: --store stats
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

    _arachna("--snapshot", "create", "--profile", "code", "--name", "stats-test")

    result = _arachna("--store", "stats")
    assert result.returncode == 0
    assert "Snapshots:" in result.stdout
    assert "Objects:" in result.stdout


# TC-060: --store gc
def test_store_gc(tmp_path, monkeypatch):
    """TC-060: --store gc garbage collects unreferenced objects."""
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

    _arachna("--snapshot", "create", "--profile", "code", "--name", "gc-test")

    result = _arachna("--store", "gc")
    assert result.returncode == 0


# TC-064: --diff --stat
def test_diff_stat(tmp_path, monkeypatch):
    """TC-064: --diff --stat shows stats only, no files written."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
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

    _arachna("--snapshot", "create", "--profile", "code", "--name", "stat-e2e")
    (tmp_path / "src" / "main.py").write_text("modified")

    result = _arachna("--diff", "--from", "stat-e2e", "--profile", "code", "--stat")
    assert result.returncode == 0
    assert "Modified:" in result.stdout
    assert "Added:" in result.stdout
    assert "Deleted:" in result.stdout

    # No files created in --stat mode
    diff_files = list(out_dir.glob("chat-diff*"))
    assert len(diff_files) == 0
