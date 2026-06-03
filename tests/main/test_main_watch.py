"""Tests for Watch CLI handlers in __main__.py."""

import json

import pytest

from arachna.__main__ import _cmd_diff, _cmd_snapshot, _cmd_store


def test_cmd_snapshot_list_empty(tmp_path, monkeypatch):
    """_cmd_snapshot with no arguments prints 'No snapshots found'."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot"])
    sys.stdout = old

    assert "No snapshots found" in out.getvalue()


def test_cmd_snapshot_delete_missing_id(tmp_path, monkeypatch):
    """_cmd_snapshot delete without id exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "delete"])


def test_cmd_snapshot_create_named(tmp_path, monkeypatch):
    """_cmd_snapshot with --name creates a named snapshot."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
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

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "--profile", "code", "--name", "test-snap"])
    sys.stdout = old

    assert "test-snap" in out.getvalue()


def test_cmd_snapshot_name_without_value(tmp_path, monkeypatch):
    """_cmd_snapshot --name without value exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "--name"])


def test_cmd_snapshot_profile_without_value(tmp_path, monkeypatch):
    """_cmd_snapshot --profile without value exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "--profile"])


def test_cmd_snapshot_list_with_data(tmp_path, monkeypatch):
    """_cmd_snapshot lists snapshots."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
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

    _cmd_snapshot(["arachna", "--snapshot", "--profile", "code", "--name", "list-test"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot"])
    sys.stdout = old

    assert "list-test" in out.getvalue()


def test_cmd_diff_no_head(tmp_path, monkeypatch):
    """_cmd_diff without HEAD exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_diff(["arachna", "--diff"])


def test_cmd_diff_from_without_value(tmp_path, monkeypatch):
    """_cmd_diff --from without value exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_diff(["arachna", "--diff", "--from"])


def test_cmd_diff_profile_without_value(tmp_path, monkeypatch):
    """_cmd_diff --profile without value exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_diff(["arachna", "--diff", "--profile"])


def test_cmd_diff_format_without_value(tmp_path, monkeypatch):
    """_cmd_diff --format without value exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_diff(["arachna", "--diff", "--format"])


def test_cmd_diff_no_changes(tmp_path, monkeypatch):
    """_cmd_diff with unchanged files prints 'No changes'."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("unchanged")
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

    _cmd_snapshot(["arachna", "--snapshot", "--profile", "code", "--name", "s1"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "s1", "--profile", "code"])
    sys.stdout = old

    assert "No changes" in out.getvalue()


def test_cmd_store_stats_empty(tmp_path, monkeypatch):
    """_cmd_store stats works on empty store."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_store(["arachna", "--store", "stats"])
    sys.stdout = old

    output = out.getvalue()
    assert "Snapshots: 0" in output
    assert "Objects: 0" in output


def test_cmd_store_gc_empty(tmp_path, monkeypatch):
    """_cmd_store gc on empty store prints 'No objects to collect'."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_store(["arachna", "--store", "gc"])
    sys.stdout = old

    assert "No objects to collect" in out.getvalue()


def test_cmd_store_invalid_cmd(tmp_path, monkeypatch):
    """_cmd_store with invalid command exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_store(["arachna", "--store", "invalid"])
