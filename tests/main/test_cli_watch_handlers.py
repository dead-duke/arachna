"""Tests for Watch CLI handlers — updated for v3.4.0."""

import json

import pytest

from arachna.cli.diff import _cmd_diff
from arachna.cli.snapshot import (
    _cmd_snapshot_create,
    _cmd_snapshot_delete,
    _cmd_snapshot_info,
    _cmd_snapshot_list,
    _cmd_snapshot_rename,
    _cmd_snapshot_update,
)
from arachna.cli.store import _cmd_store_gc, _cmd_store_stats


def _make_snap_create_args(name, profile):
    from argparse import Namespace

    return Namespace(name=name, profile=profile)


def _make_snap_update_args(sid, profile=None):
    from argparse import Namespace

    return Namespace(id=sid, profile=profile)


def _make_snap_delete_args(sid):
    from argparse import Namespace

    return Namespace(id=sid)


def _make_snap_info_args(sid, profile_only=False, stats_only=False):
    from argparse import Namespace

    return Namespace(id=sid, profile_only=profile_only, stats_only=stats_only)


def _make_snap_rename_args(old, new):
    from argparse import Namespace

    return Namespace(old=old, new=new)


def _make_diff_args(
    from_snapshot=None,
    to=None,
    all=False,
    profile=None,
    stat=False,
    flat=False,
    fmt=None,
    mode=None,
    compress=False,
    output_dir=None,
    query=None,
):
    from argparse import Namespace

    return Namespace(
        from_snapshot=from_snapshot,
        to=to,
        all=all,
        profile=profile,
        stat=stat,
        flat=flat,
        format=fmt,
        mode=mode,
        compress=compress,
        output_dir=output_dir,
        query=query,
    )


def _make_store_args():
    from argparse import Namespace

    return Namespace()


def test_cmd_snapshot_list_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_list(_make_store_args(), {})
    sys.stdout = old

    assert "No snapshots found" in out.getvalue()


def test_cmd_snapshot_list_with_data(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("list-test", "code"), config)

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_list(_make_store_args(), config)
    sys.stdout = old

    assert "list-test" in out.getvalue()


def test_cmd_snapshot_create_named(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_create(_make_snap_create_args("test-snap", "code"), config)
    sys.stdout = old

    assert "test-snap" in out.getvalue()


def test_cmd_snapshot_duplicate_name(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("dup-test", "code"), config)

    with pytest.raises(SystemExit):
        _cmd_snapshot_create(_make_snap_create_args("dup-test", "code"), config)


def test_cmd_snapshot_update(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("upd-test", "code"), config)

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_update(_make_snap_update_args("upd-test"), config)
    sys.stdout = old

    assert "updated" in out.getvalue()


def test_cmd_snapshot_update_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot_update(_make_snap_update_args("nonexistent"), {})


def test_cmd_snapshot_delete(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("del-test", "code"), config)
    _cmd_snapshot_delete(_make_snap_delete_args("del-test"), config)


def test_cmd_snapshot_info_full(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("info-test", "code"), config)

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_info(_make_snap_info_args("info-test"), config)
    sys.stdout = old

    output = out.getvalue()
    assert "Snapshot: info-test" in output
    assert "Created:" in output
    assert "Files:" in output
    assert "Profile:" in output


def test_cmd_snapshot_info_profile_only(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("prof-test", "code"), config)

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_info(_make_snap_info_args("prof-test", profile_only=True), config)
    sys.stdout = old

    output = out.getvalue()
    assert "Profile:" in output
    assert "max_tokens:" in output
    assert "Snapshot:" not in output


def test_cmd_snapshot_info_stats_only(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("stats-info", "code"), config)

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_info(_make_snap_info_args("stats-info", stats_only=True), config)
    sys.stdout = old

    output = out.getvalue()
    assert "Files:" in output
    assert "Pre-commands:" in output
    assert "Profile:" not in output


def test_cmd_snapshot_rename(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("old-name", "code"), config)

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_rename(_make_snap_rename_args("old-name", "new-name"), config)
    sys.stdout = old

    assert "renamed" in out.getvalue()

    out2 = StringIO()
    sys.stdout = out2
    _cmd_snapshot_list(_make_store_args(), config)
    sys.stdout = old
    assert "new-name" in out2.getvalue()
    assert "old-name" not in out2.getvalue()


def test_cmd_snapshot_rename_duplicate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    from arachna.store import create_snapshot as store_create

    store_create({"a.py": "x"}, name="first")
    store_create({"b.py": "y"}, name="second")

    with pytest.raises(SystemExit):
        _cmd_snapshot_rename(_make_snap_rename_args("first", "second"), {})


def test_cmd_diff_no_head(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_diff(_make_diff_args(), {})


def test_cmd_diff_no_changes(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("s1", "code"), config)

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_make_diff_args(from_snapshot="s1", profile="code"), config)
    sys.stdout = old

    assert "No changes" in out.getvalue()


def test_cmd_diff_stat_only(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("stat-test", "code"), config)
    (tmp_path / "src" / "main.py").write_text("modified")

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_make_diff_args(from_snapshot="stat-test", profile="code", stat=True), config)
    sys.stdout = old

    output = out.getvalue()
    assert "Modified:" in output
    assert "Added:" in output
    assert "Deleted:" in output


def test_cmd_diff_single_snapshot_auto_select(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("only-snap", "code"), config)

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_make_diff_args(), config)
    sys.stdout = old

    assert "No changes" in out.getvalue()


def test_cmd_diff_multiple_snapshots_hint(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("snap-a", "code"), config)
    _cmd_snapshot_create(_make_snap_create_args("snap-b", "code"), config)

    with pytest.raises(SystemExit):
        _cmd_diff(_make_diff_args(), config)


def test_cmd_diff_legacy_profile_error(tmp_path, monkeypatch):
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
        _cmd_diff(_make_diff_args(from_snapshot="old-legacy"), {})


def test_cmd_diff_with_to_flag(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("v1", "code"), config)
    (tmp_path / "src" / "main.py").write_text("version 2")
    _cmd_snapshot_create(_make_snap_create_args("v2", "code"), config)

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_make_diff_args(from_snapshot="v1", to="v2"), config)
    sys.stdout = old

    output = out.getvalue()
    assert "chat-diff" in output


def test_cmd_diff_flat_flag(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("flat-test", "code"), config)
    (tmp_path / "src" / "main.py").write_text("modified")

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_make_diff_args(from_snapshot="flat-test", flat=True), config)
    sys.stdout = old

    output = out.getvalue()
    assert "chat-diff" in output


def test_cmd_diff_stat_with_renamed(tmp_path, monkeypatch):
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

    config = json.loads((tmp_path / ".arachna.json").read_text())
    _cmd_snapshot_create(_make_snap_create_args("stat-v1", "code"), config)
    (tmp_path / "src" / "main.py").unlink()
    (tmp_path / "src" / "renamed.py").write_text("print('hello')")
    _cmd_snapshot_create(_make_snap_create_args("stat-v2", "code"), config)

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_make_diff_args(from_snapshot="stat-v1", to="stat-v2", stat=True), config)
    sys.stdout = old

    output = out.getvalue()
    assert "Renamed:" in output


def test_cmd_store_stats_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_store_stats(_make_store_args(), {})
    sys.stdout = old

    output = out.getvalue()
    assert "Snapshots: 0" in output
    assert "Objects: 0" in output


def test_cmd_store_gc_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_store_gc(_make_store_args(), {})
    sys.stdout = old

    assert "No objects to collect" in out.getvalue()
