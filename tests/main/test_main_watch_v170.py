"""Tests for v1.7.0 Watch CLI handlers — now in cli_watch.py."""

import json

import pytest

from arachna.cli_watch import _cmd_diff, _cmd_snapshot


def test_cmd_snapshot_info_full(tmp_path, monkeypatch):
    """--snapshot info <id> shows full details."""
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
                        "pre_commands": ["echo hello"],
                    }
                },
            }
        )
    )

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "info-test"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "info", "info-test"])
    sys.stdout = old

    output = out.getvalue()
    assert "Snapshot: info-test" in output
    assert "Created:" in output
    assert "Files:" in output
    assert "Profile:" in output
    assert "directories:" in output
    assert "patterns:" in output


def test_cmd_snapshot_info_profile_only(tmp_path, monkeypatch):
    """--snapshot info <id> --profile shows profile only."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "prof-test"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "info", "prof-test", "--profile"])
    sys.stdout = old

    output = out.getvalue()
    assert "Profile:" in output
    assert "max_tokens:" in output
    assert "Snapshot:" not in output


def test_cmd_snapshot_info_stats_only(tmp_path, monkeypatch):
    """--snapshot info <id> --stats shows stats only."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "stats-info"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "info", "stats-info", "--stats"])
    sys.stdout = old

    output = out.getvalue()
    assert "Files:" in output
    assert "Pre-commands:" in output
    assert "Profile:" not in output


def test_cmd_snapshot_info_missing_id(tmp_path, monkeypatch):
    """--snapshot info without id exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "info"])


def test_cmd_snapshot_info_not_found(tmp_path, monkeypatch):
    """--snapshot info for non-existent snapshot exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "info", "nonexistent"])


def test_cmd_snapshot_rename(tmp_path, monkeypatch):
    """--snapshot rename <old> <new> renames snapshot."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "old-name"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "rename", "old-name", "new-name"])
    sys.stdout = old

    assert "renamed" in out.getvalue()

    out2 = StringIO()
    sys.stdout = out2
    _cmd_snapshot(["arachna", "--snapshot", "list"])
    sys.stdout = old
    assert "new-name" in out2.getvalue()
    assert "old-name" not in out2.getvalue()


def test_cmd_snapshot_rename_missing_args(tmp_path, monkeypatch):
    """--snapshot rename without enough args exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "rename", "only-one"])


def test_cmd_snapshot_rename_duplicate(tmp_path, monkeypatch):
    """--snapshot rename to existing name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    from arachna.store import create_snapshot as store_create

    store_create({"a.py": "x"}, name="first")
    store_create({"b.py": "y"}, name="second")

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "rename", "first", "second"])


def test_cmd_snapshot_list_no_duplicate_column(tmp_path, monkeypatch):
    """--snapshot list shows id once, not duplicate id/name columns."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "list-snap"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "list"])
    sys.stdout = old

    output = out.getvalue()
    assert "Snapshots:" in output
    assert "list-snap" in output
    assert output.count("list-snap") == 1


def test_cmd_diff_with_to_flag(tmp_path, monkeypatch):
    """--diff --from A --to B does cross-snapshot diff."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("version 1")
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "v1"])
    (tmp_path / "src" / "main.py").write_text("version 2")
    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "v2"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "v1", "--to", "v2"])
    sys.stdout = old

    output = out.getvalue()
    assert "chat-diff" in output


def test_cmd_diff_flat_flag(tmp_path, monkeypatch):
    """--diff --flat produces flat output without grouping."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "flat-test"])
    (tmp_path / "src" / "main.py").write_text("modified")

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "flat-test", "--flat"])
    sys.stdout = old

    output = out.getvalue()
    assert "chat-diff" in output


def test_cmd_diff_stat_with_renamed(tmp_path, monkeypatch):
    """--diff --stat shows renamed/moved counts."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "stat-v1"])
    (tmp_path / "src" / "main.py").unlink()
    (tmp_path / "src" / "renamed.py").write_text("print('hello')")
    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "stat-v2"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "stat-v1", "--to", "stat-v2", "--stat"])
    sys.stdout = old

    output = out.getvalue()
    assert "Renamed:" in output


def test_cmd_diff_to_missing_value(tmp_path, monkeypatch):
    """--diff --to without value exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_diff(["arachna", "--diff", "--to"])


def test_cmd_snapshot_usage_includes_new_commands(tmp_path, monkeypatch):
    """--snapshot usage hint includes info and rename commands."""
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

    output = out.getvalue()
    assert "info <id>" in output
    assert "rename <old> <new>" in output
