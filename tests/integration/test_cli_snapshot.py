import json

from tests.integration.conftest import _arachna


def test_snapshot_create_and_list(tmp_path):
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
    result = _arachna(
        "snapshot", "create", "--profile", "code", "--name", "list-test", cwd=tmp_path
    )
    assert result.returncode == 0
    result = _arachna("snapshot", "list", cwd=tmp_path)
    assert result.returncode == 0
    assert "list-test" in result.stdout


def test_snapshot_named(tmp_path):
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
    result = _arachna("snapshot", "create", "--profile", "code", "--name", "my-snap", cwd=tmp_path)
    assert result.returncode == 0
    assert "my-snap" in result.stdout


def test_snapshot_delete(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "to-delete", cwd=tmp_path)
    result = _arachna("snapshot", "delete", "to-delete", cwd=tmp_path)
    assert result.returncode == 0
    result = _arachna("snapshot", "list", cwd=tmp_path)
    assert "to-delete" not in result.stdout


def test_snapshot_delete_not_found(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    result = _arachna("snapshot", "delete", "nonexistent", cwd=tmp_path)
    assert result.returncode == 1


def test_diff_modified(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "snap1", cwd=tmp_path)
    (tmp_path / "src" / "main.py").write_text("modified")
    result = _arachna("diff", "--from", "snap1", "--profile", "code", cwd=tmp_path)
    assert result.returncode == 0
    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "REMOVED" in content or "ADDED" in content


def test_diff_no_snapshot(tmp_path):
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
    result = _arachna("diff", "--profile", "code", cwd=tmp_path)
    assert result.returncode == 1


def test_store_stats(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "stats-test", cwd=tmp_path)
    result = _arachna("store", "stats", cwd=tmp_path)
    assert result.returncode == 0
    assert "Snapshots:" in result.stdout
    assert "Objects:" in result.stdout


def test_store_gc(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "gc-test", cwd=tmp_path)
    result = _arachna("store", "gc", cwd=tmp_path)
    assert result.returncode == 0


def test_diff_stat(tmp_path):
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
    _arachna("snapshot", "create", "--profile", "code", "--name", "stat-e2e", cwd=tmp_path)
    (tmp_path / "src" / "main.py").write_text("modified")
    result = _arachna("diff", "--from", "stat-e2e", "--profile", "code", "--stat", cwd=tmp_path)
    assert result.returncode == 0
    assert "Modified:" in result.stdout
    assert "Added:" in result.stdout
    assert "Deleted:" in result.stdout
    diff_files = list(out_dir.glob("chat-diff*"))
    assert len(diff_files) == 0
