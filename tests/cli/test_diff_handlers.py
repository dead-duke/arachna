"""Tests for diff CLI handlers — stat, format, modes, compress, cross-snapshot."""

import json
from io import StringIO

import pytest

from arachna.cli.diff import _cmd_diff
from arachna.cli.snapshot import _cmd_snapshot_create


def _snap_create(name, profile):
    from argparse import Namespace

    return Namespace(name=name, profile=profile)


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
    (tmp_path / "mysrc" / "main.py").write_text("modified v2")
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
    assert "Tokens:" in output


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
    from arachna.snapshot.store import _store_root, write_object

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
    (tmp_path / "mysrc" / "main.py").write_text("modified flat")
    _cmd_snapshot_create(_snap_create("flat-test", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("original")
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_diff(_diff_args(fr="flat-test", profile="code", flat=True), config)
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


def test_cmd_diff_format_xml(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("original")
    _cmd_snapshot_create(_snap_create("xml-test", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("modified for xml")
    _cmd_diff(_diff_args(fr="xml-test", profile="code", fmt="xml"), config)
    files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert '<file path="' in content


def test_cmd_diff_mode_structural(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("def foo():\n    return 1\n")
    _cmd_snapshot_create(_snap_create("struct-cov", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("def foo():\n    return 2\n")
    _cmd_diff(_diff_args(fr="struct-cov", profile="code", mode="structural"), config)
    files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "MODIFIED" in content or "modified" in content.lower()


def test_cmd_diff_mode_repo_map(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text(
        "def foo():\n    return 1\n\ndef bar():\n    return 2\n"
    )
    _cmd_snapshot_create(_snap_create("rm-cov", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text(
        "def foo():\n    return 3\n\ndef bar():\n    return 4\n"
    )
    _cmd_diff(_diff_args(fr="rm-cov", profile="code", mode="repo-map"), config)
    files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "def foo():" in content


def test_cmd_diff_compress(tmp_path, make_config):
    config = make_config(tmp_path, dirs=["mysrc"])
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("original\n\n\n\nspaces")
    _cmd_snapshot_create(_snap_create("comp-cov", "code"), config)
    (tmp_path / "mysrc" / "main.py").write_text("modified\n\n\n\nafter")
    _cmd_diff(_diff_args(fr="comp-cov", profile="code", compress=True), config)
    files = list((tmp_path / "out").glob("chat-diff*"))
    assert len(files) >= 1
