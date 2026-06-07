"""Tests for Watch CLI handlers in cli_watch.py."""

import json

import pytest

from arachna.cli_watch import _cmd_diff, _cmd_snapshot, _cmd_store


def test_cmd_snapshot_usage_hint(tmp_path, monkeypatch):
    """_cmd_snapshot with no arguments shows usage hint."""
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

    assert "Usage:" in out.getvalue()
    assert "list" in out.getvalue()
    assert "create" in out.getvalue()
    assert "update" in out.getvalue()
    assert "delete" in out.getvalue()


def test_cmd_snapshot_delete_missing_id(tmp_path, monkeypatch):
    """_cmd_snapshot delete without id exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "delete"])


def test_cmd_snapshot_create_named(tmp_path, monkeypatch):
    """_cmd_snapshot create --profile X --name Y creates a named snapshot."""
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
    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "test-snap"])
    sys.stdout = old

    assert "test-snap" in out.getvalue()


def test_cmd_snapshot_create_name_required(tmp_path, monkeypatch):
    """_cmd_snapshot create without --name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code"])


def test_cmd_snapshot_name_without_value(tmp_path, monkeypatch):
    """_cmd_snapshot create --name without value exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name"])


def test_cmd_snapshot_list_empty(tmp_path, monkeypatch):
    """_cmd_snapshot list with no snapshots prints 'No snapshots found'."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "list"])
    sys.stdout = old

    assert "No snapshots found" in out.getvalue()


def test_cmd_snapshot_list_with_data(tmp_path, monkeypatch):
    """_cmd_snapshot list shows snapshots."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "list-test"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "list"])
    sys.stdout = old

    assert "list-test" in out.getvalue()


def test_cmd_snapshot_duplicate_name(tmp_path, monkeypatch):
    """_cmd_snapshot create with duplicate name exits 1."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "dup-test"])

    with pytest.raises(SystemExit):
        _cmd_snapshot(
            ["arachna", "--snapshot", "create", "--profile", "code", "--name", "dup-test"]
        )


def test_cmd_diff_no_head(tmp_path, monkeypatch):
    """_cmd_diff without snapshots exits 1."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "s1"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "s1", "--profile", "code"])
    sys.stdout = old

    assert "No changes" in out.getvalue()


def test_cmd_diff_stat_only(tmp_path, monkeypatch):
    """_cmd_diff --stat shows stats only."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "stat-test"])
    (tmp_path / "src" / "main.py").write_text("modified")

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "stat-test", "--profile", "code", "--stat"])
    sys.stdout = old

    output = out.getvalue()
    assert "Modified:" in output
    assert "Added:" in output
    assert "Deleted:" in output


def test_cmd_diff_single_snapshot_auto_select(tmp_path, monkeypatch):
    """_cmd_diff without --from auto-selects when only one snapshot exists."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "only-snap"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff"])
    sys.stdout = old

    assert "No changes" in out.getvalue()


def test_cmd_diff_multiple_snapshots_hint(tmp_path, monkeypatch):
    """_cmd_diff without --from with multiple snapshots shows hint and exits 1."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "snap-a"])
    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "snap-b"])

    with pytest.raises(SystemExit):
        _cmd_diff(["arachna", "--diff"])


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


def test_cmd_snapshot_update(tmp_path, monkeypatch):
    """_cmd_snapshot update re-scans and updates a snapshot."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "upd-test"])

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "update", "upd-test"])
    sys.stdout = old

    assert "updated" in out.getvalue()


def test_cmd_snapshot_update_not_found(tmp_path, monkeypatch):
    """_cmd_snapshot update for non-existent snapshot exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "update", "nonexistent"])


def test_cmd_snapshot_update_no_id(tmp_path, monkeypatch):
    """_cmd_snapshot update without id exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "update"])


def test_cmd_snapshot_update_invalid_id(tmp_path, monkeypatch):
    """_cmd_snapshot update with flag as id exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "update", "--profile"])


def test_cmd_diff_compress_flag(tmp_path, monkeypatch):
    """_cmd_diff with --compress applies compress to profile."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "cmpr-test"])
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(["arachna", "--diff", "--from", "cmpr-test", "--profile", "code", "--compress"])
    sys.stdout = old

    files = list(out_dir.glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


def test_cmd_diff_with_output_dir_short_flag(tmp_path, monkeypatch):
    """_cmd_diff with -o flag writes to custom directory."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "od-test"])
    (tmp_path / "src" / "main.py").write_text("modified for -o test")

    custom_dir = tmp_path / "custom_diff"
    _cmd_diff(
        ["arachna", "--diff", "--from", "od-test", "--profile", "code", "-o", str(custom_dir)]
    )

    files = list(custom_dir.glob("chat-diff*"))
    assert len(files) >= 1

    default_files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(default_files) == 0


def test_cmd_diff_output_dir_long_flag(tmp_path, monkeypatch):
    """_cmd_diff with --output-dir flag writes to custom directory."""
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

    _cmd_snapshot(["arachna", "--snapshot", "create", "--profile", "code", "--name", "odl-test"])
    (tmp_path / "src" / "main.py").write_text("modified for --output-dir test")

    custom_dir = tmp_path / "custom_long"
    _cmd_diff(
        [
            "arachna",
            "--diff",
            "--from",
            "odl-test",
            "--profile",
            "code",
            "--output-dir",
            str(custom_dir),
        ]
    )

    files = list(custom_dir.glob("chat-diff*"))
    assert len(files) >= 1


def test_cmd_diff_legacy_profile_error(tmp_path, monkeypatch):
    """_cmd_diff with legacy string profile in manifest exits 1."""
    import json

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    from arachna.store import _store_root, write_object

    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    test_hash = write_object(b"x")
    old_manifest = {
        "id": "old-legacy",
        "name": "old-legacy",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"a.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "old-legacy.json").write_text(json.dumps(old_manifest))

    with pytest.raises(SystemExit):
        _cmd_diff(["arachna", "--diff", "--from", "old-legacy"])


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


def test_cmd_snapshot_info_invalid_id_flag(tmp_path, monkeypatch):
    """--snapshot info with flag-like id exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "info", "--profile"])


def test_cmd_snapshot_info_not_found_error(tmp_path, monkeypatch):
    """--snapshot info for non-existent snapshot exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "info", "nonexistent"])


def test_cmd_snapshot_info_list_snapshots_error(tmp_path, monkeypatch):
    """--snapshot info when list_snapshots raises an exception exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    from unittest.mock import patch

    with (
        patch("arachna.store.list_snapshots", side_effect=OSError("disk error")),
        pytest.raises(SystemExit),
    ):
        _cmd_snapshot(["arachna", "--snapshot", "info", "some-id"])


def test_cmd_snapshot_rename_missing_old(tmp_path, monkeypatch):
    """--snapshot rename without old name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "rename"])


def test_cmd_snapshot_rename_missing_new(tmp_path, monkeypatch):
    """--snapshot rename without new name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "rename", "old-name"])


def test_cmd_snapshot_rename_old_is_flag(tmp_path, monkeypatch):
    """--snapshot rename with flag as old name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "rename", "--profile", "new-name"])


def test_cmd_snapshot_rename_new_is_flag(tmp_path, monkeypatch):
    """--snapshot rename with flag as new name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "rename", "old-name", "--profile"])


def test_cmd_snapshot_info_profile_legacy_format(tmp_path, monkeypatch):
    """--snapshot info --profile with legacy string profile format."""
    import json as _json

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        _json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    from arachna.store import _store_root, write_object

    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    test_hash = write_object(b"legacy content")
    old_manifest = {
        "id": "legacy-prof",
        "name": "legacy-prof",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"a.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "legacy-prof.json").write_text(_json.dumps(old_manifest))

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "info", "legacy-prof", "--profile"])
    sys.stdout = old

    assert "legacy format" in out.getvalue()
