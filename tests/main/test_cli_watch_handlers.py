"""Tests for Watch CLI handlers."""

import json
from io import StringIO

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


def _snap_create(name, profile):
    from argparse import Namespace

    return Namespace(name=name, profile=profile)


def _snap_update(sid, profile=None):
    from argparse import Namespace

    return Namespace(id=sid, profile=profile)


def _snap_delete(sid):
    from argparse import Namespace

    return Namespace(id=sid)


def _snap_info(sid, profile_only=False, stats_only=False):
    from argparse import Namespace

    return Namespace(id=sid, profile_only=profile_only, stats_only=stats_only)


def _snap_rename(old, new):
    from argparse import Namespace

    return Namespace(old=old, new=new)


def _diff_args(
    fr=None,
    to=None,
    all=False,
    profile=None,
    stat=False,
    flat=False,
    fmt=None,
    mode=None,
    compress=False,
):
    from argparse import Namespace

    return Namespace(
        from_snapshot=fr,
        to=to,
        all=all,
        profile=profile,
        stat=stat,
        flat=flat,
        format=fmt,
        mode=mode,
        compress=compress,
        output_dir=None,
        query=None,
    )


def _store_args():
    from argparse import Namespace

    return Namespace()


def test_cmd_snapshot_list_empty(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_list(_store_args(), config)
    sys.stdout = old
    assert "No snapshots found" in out.getvalue()


def test_cmd_snapshot_list_with_data(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("list-test", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_list(_store_args(), config)
    sys.stdout = old
    assert "list-test" in out.getvalue()


def test_cmd_snapshot_create_named(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_create(_snap_create("test-snap", "code"), config)
    sys.stdout = old
    assert "test-snap" in out.getvalue()


def test_cmd_snapshot_duplicate_name(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("dup-test", "code"), config)
    with pytest.raises(SystemExit):
        _cmd_snapshot_create(_snap_create("dup-test", "code"), config)


def test_cmd_snapshot_update(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("upd-test", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_update(_snap_update("upd-test"), config)
    sys.stdout = old
    assert "updated" in out.getvalue()


def test_cmd_snapshot_update_not_found(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_snapshot_update(_snap_update("nonexistent"), config)


def test_cmd_snapshot_delete(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("del-test", "code"), config)
    _cmd_snapshot_delete(_snap_delete("del-test"), config)


def test_cmd_snapshot_info_full(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    config["profiles"]["code"]["pre_commands"] = ["echo hello"]
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("info-test", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_info(_snap_info("info-test"), config)
    sys.stdout = old
    output = out.getvalue()
    assert "Snapshot: info-test" in output
    assert "Created:" in output
    assert "Files:" in output
    assert "Profile:" in output


def test_cmd_snapshot_info_profile_only(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("prof-test", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_info(_snap_info("prof-test", profile_only=True), config)
    sys.stdout = old
    output = out.getvalue()
    assert "Profile:" in output
    assert "max_tokens:" in output
    assert "Snapshot:" not in output


def test_cmd_snapshot_info_stats_only(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("stats-info", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_info(_snap_info("stats-info", stats_only=True), config)
    sys.stdout = old
    output = out.getvalue()
    assert "Files:" in output
    assert "Pre-commands:" in output
    assert "Profile:" not in output


def test_cmd_snapshot_rename(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("old-name", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_rename(_snap_rename("old-name", "new-name"), config)
    sys.stdout = old
    assert "renamed" in out.getvalue()
    out2 = StringIO()
    sys.stdout = out2
    _cmd_snapshot_list(_store_args(), config)
    sys.stdout = old
    assert "new-name" in out2.getvalue()
    assert "old-name" not in out2.getvalue()


def test_cmd_snapshot_rename_duplicate(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    from arachna.watch.store import create_snapshot as store_create

    store_create({"a.py": "x"}, name="first", root=tmp_path)
    store_create({"b.py": "y"}, name="second", root=tmp_path)
    with pytest.raises(SystemExit):
        _cmd_snapshot_rename(_snap_rename("first", "second"), config)


def test_cmd_diff_no_head(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_diff(_diff_args(), config)


def test_cmd_diff_no_changes(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("unchanged")
    _cmd_snapshot_create(_snap_create("s1", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_diff_args(fr="s1", profile="code"), config)
    sys.stdout = old
    assert "No changes" in out.getvalue()


def test_cmd_diff_stat_only(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("original")
    _cmd_snapshot_create(_snap_create("stat-test", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("modified")
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_diff_args(fr="stat-test", profile="code", stat=True), config)
    sys.stdout = old
    output = out.getvalue()
    assert "Modified:" in output
    assert "Added:" in output
    assert "Deleted:" in output


def test_cmd_diff_single_snapshot_auto_select(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("original")
    _cmd_snapshot_create(_snap_create("only-snap", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_diff_args(), config)
    sys.stdout = old
    assert "No changes" in out.getvalue()


def test_cmd_diff_multiple_snapshots_hint(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("original")
    _cmd_snapshot_create(_snap_create("snap-a", "code"), config)
    _cmd_snapshot_create(_snap_create("snap-b", "code"), config)
    with pytest.raises(SystemExit):
        _cmd_diff(_diff_args(), config)


def test_cmd_diff_legacy_profile_error(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    from arachna.watch.store import _store_root, write_object

    store_dir = _store_root(tmp_path)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    test_hash = write_object(b"x", root=tmp_path)
    old_manifest = {
        "id": "old-legacy",
        "name": "old-legacy",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"a.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "old-legacy.json").write_text(json.dumps(old_manifest))
    with pytest.raises(SystemExit):
        _cmd_diff(_diff_args(fr="old-legacy"), config)


def test_cmd_diff_with_to_flag(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("version 1")
    _cmd_snapshot_create(_snap_create("v1", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("version 2")
    _cmd_snapshot_create(_snap_create("v2", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_diff_args(fr="v1", to="v2"), config)
    sys.stdout = old
    output = out.getvalue()
    assert "chat-diff" in output


def test_cmd_diff_flat_flag(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("original")
    _cmd_snapshot_create(_snap_create("flat-test", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("modified")
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_diff_args(fr="flat-test", flat=True), config)
    sys.stdout = old
    output = out.getvalue()
    assert "chat-diff" in output


def test_cmd_diff_stat_with_renamed(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hello')")
    _cmd_snapshot_create(_snap_create("stat-v1", "code"), config)
    (tmp_path / "mysrc" / "main.py").unlink()
    (tmp_path / "mysrc" / "renamed.py").write_text("print('hello')")
    _cmd_snapshot_create(_snap_create("stat-v2", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_diff_args(fr="stat-v1", to="stat-v2", stat=True), config)
    sys.stdout = old
    output = out.getvalue()
    assert "Renamed:" in output


def test_cmd_store_stats_empty(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_store_stats(_store_args(), config)
    sys.stdout = old
    output = out.getvalue()
    assert "Snapshots: 0" in output
    assert "Objects: 0" in output


def test_cmd_store_gc_empty(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_store_gc(_store_args(), config)
    sys.stdout = old
    assert "No objects to collect" in out.getvalue()
