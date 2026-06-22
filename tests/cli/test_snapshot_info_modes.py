"""Tests for snapshot info — --profile, --stats, legacy format."""

import json
from io import StringIO

from arachna.cli.snapshot import _cmd_snapshot_create, _cmd_snapshot_info
from arachna.snapshot.store import _store_root, write_object


def _snap_create(name, profile):
    from argparse import Namespace

    return Namespace(name=name, profile=profile)


def _snap_info(sid, profile_only=False, stats_only=False):
    from argparse import Namespace

    return Namespace(id=sid, profile_only=profile_only, stats_only=stats_only)


def test_snapshot_info_profile_only(tmp_path, make_config):
    """--profile shows only profile section."""
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
    assert "Snapshot:" not in output


def test_snapshot_info_stats_only(tmp_path, make_config):
    """--stats shows only file/pre-commands counts."""
    config = make_config(tmp_path, dirs=["mysrc"])
    code_prof = config.profiles["code"]
    code_prof.pre_commands = ["echo hello"]
    (tmp_path / "mysrc").mkdir()
    (tmp_path / "mysrc" / "main.py").write_text("print('hi')")
    _cmd_snapshot_create(_snap_create("stats-test", "code"), config)
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_info(_snap_info("stats-test", stats_only=True), config)
    sys.stdout = old
    output = out.getvalue()
    assert "Files:" in output
    assert "Pre-commands:" in output
    assert "Profile:" not in output


def test_snapshot_info_legacy_profile_string(tmp_path, make_config):
    """Legacy snapshot with string profile shows legacy marker."""
    config = make_config(tmp_path, profiles={})
    store_dir = _store_root(tmp_path)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    test_hash = write_object(b"legacy content", root=tmp_path)
    old_manifest = {
        "id": "old-legacy",
        "name": "old-legacy",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"a.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "old-legacy.json").write_text(json.dumps(old_manifest))
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot_info(_snap_info("old-legacy"), config)
    sys.stdout = old
    assert "legacy format" in out.getvalue()
