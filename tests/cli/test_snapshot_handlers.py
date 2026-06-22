"""Tests for snapshot CLI handlers — create, list, update, delete, info, rename."""

from io import StringIO

import pytest

from arachna.cli.snapshot import (
    _cmd_snapshot_create,
    _cmd_snapshot_delete,
    _cmd_snapshot_info,
    _cmd_snapshot_list,
    _cmd_snapshot_rename,
    _cmd_snapshot_update,
)


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


def _store_args():
    from argparse import Namespace

    return Namespace()


# -- snapshot list --


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


# -- snapshot create --


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


# -- snapshot update --


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


def test_cmd_snapshot_update_with_profile(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("upd-cov", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_update(_snap_update("upd-cov", "code"), config)
    sys.stdout = old
    assert "updated" in out.getvalue()


def test_cmd_snapshot_update_not_found(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_snapshot_update(_snap_update("nonexistent"), config)


# -- snapshot delete --


def test_cmd_snapshot_delete(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("del-test", "code"), config)
    _cmd_snapshot_delete(_snap_delete("del-test"), config)


# -- snapshot info --


def test_cmd_snapshot_info_full(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    code_prof = config.profiles["code"]
    code_prof.pre_commands = ["echo hello"]
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
    assert "Pre-commands:" in output
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


# -- snapshot rename --


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
    from arachna.snapshot.store import create_snapshot as store_create

    store_create({"a.py": "x"}, name="first", root=tmp_path)
    store_create({"b.py": "y"}, name="second", root=tmp_path)
    with pytest.raises(SystemExit):
        _cmd_snapshot_rename(_snap_rename("first", "second"), config)
