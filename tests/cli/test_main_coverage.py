"""Coverage for __main__.py — error paths, edge cases."""

import json
from argparse import Namespace

import pytest

from arachna.cli._helpers import print_collected, write_manifest
from arachna.cli.collect import _cmd_collect_clean, _cmd_collect_profile, _cmd_collect_validate
from arachna.cli.diff import _cmd_diff
from arachna.cli.snapshot import (
    _cmd_snapshot_create,
    _cmd_snapshot_delete,
    _cmd_snapshot_info,
    _cmd_snapshot_rename,
    _cmd_snapshot_update,
)


def _config(tmp_path, profiles=None):
    return {
        "project_name": "test",
        "output_dir": str(tmp_path / "out"),
        "_root": str(tmp_path),
        "profiles": profiles or {"c": {"directories": ["mysrc"], "max_tokens": 100}},
    }


def test_snapshot_create_no_name(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    with pytest.raises(SystemExit):
        _cmd_snapshot_create(Namespace(name=None, profile="c"), config)


def test_snapshot_create_invalid_name(tmp_path, make_config):
    config = make_config(tmp_path)
    with pytest.raises(SystemExit):
        _cmd_snapshot_create(Namespace(name="../../etc", profile="c"), config)


def test_snapshot_create_profile_not_found(tmp_path, make_config):
    config = make_config(tmp_path, profiles={"x": {"command": "echo hi", "max_tokens": 100}})
    with pytest.raises(SystemExit):
        _cmd_snapshot_create(Namespace(name="test", profile="nonexistent"), config)


def test_snapshot_delete_invalid_id(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_snapshot_delete(Namespace(id="../../etc"), config)


def test_snapshot_info_invalid_id(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_snapshot_info(Namespace(id="../../etc", profile_only=False, stats_only=False), config)


def test_snapshot_info_not_found(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_snapshot_info(Namespace(id="nonexist", profile_only=False, stats_only=False), config)


def test_snapshot_rename_invalid_old(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_snapshot_rename(Namespace(old="../../etc", new="ok"), config)


def test_snapshot_rename_invalid_new(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_snapshot_rename(Namespace(old="ok", new="../../etc"), config)


def test_snapshot_update_invalid_id(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_snapshot_update(Namespace(id="../../etc", profile=None), config)


def test_snapshot_update_not_found(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_snapshot_update(Namespace(id="nonexist", profile=None), config)


def test_snapshot_update_profile_not_found(tmp_path, make_config):
    config = make_config(tmp_path, profiles={"x": {"command": "echo hi", "max_tokens": 100}})
    from arachna.snapshot.store import create_snapshot as store_create

    store_create({"a.py": "x"}, name="test-snap", root=tmp_path)
    with pytest.raises(SystemExit):
        _cmd_snapshot_update(Namespace(id="test-snap", profile="nonexistent"), config)


def test_diff_all_and_from_conflict(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_diff(
            Namespace(
                from_snapshot="x",
                to=None,
                all=True,
                profile=None,
                stat=False,
                flat=False,
                format=None,
                mode=None,
                compress=False,
                output_dir=None,
                query=None,
            ),
            config,
        )


def test_diff_no_snapshots(tmp_path, make_config):
    config = make_config(tmp_path, profiles={})
    with pytest.raises(SystemExit):
        _cmd_diff(
            Namespace(
                from_snapshot=None,
                to=None,
                all=False,
                profile=None,
                stat=False,
                flat=False,
                format=None,
                mode=None,
                compress=False,
                output_dir=None,
                query=None,
            ),
            config,
        )


def test_diff_profile_not_found(tmp_path, make_config):
    config = make_config(tmp_path, profiles={"x": {"command": "echo hi", "max_tokens": 100}})
    from arachna.snapshot.store import create_snapshot as store_create

    store_create({"a.py": "x"}, name="test-snap", root=tmp_path)
    with pytest.raises(SystemExit):
        _cmd_diff(
            Namespace(
                from_snapshot="test-snap",
                to=None,
                all=False,
                profile="nonexistent",
                stat=False,
                flat=False,
                format=None,
                mode=None,
                compress=False,
                output_dir=None,
                query=None,
            ),
            config,
        )


def test_diff_all_profile_not_found(tmp_path, make_config):
    config = make_config(tmp_path, profiles={"x": {"command": "echo hi", "max_tokens": 100}})
    with pytest.raises(SystemExit):
        _cmd_diff(
            Namespace(
                from_snapshot=None,
                to=None,
                all=True,
                profile="nonexistent",
                stat=False,
                flat=False,
                format=None,
                mode=None,
                compress=False,
                output_dir=None,
                query=None,
            ),
            config,
        )


def test_collect_profile_not_found(tmp_path, make_config):
    config = make_config(tmp_path, profiles={"x": {"command": "echo hi", "max_tokens": 100}})
    with pytest.raises(SystemExit):
        _cmd_collect_profile(
            Namespace(
                profile="nonexistent",
                all=False,
                dry_run=False,
                merge=False,
                verbose=False,
                incremental=False,
                compress=False,
                format=None,
                query=None,
                mode="full",
                no_pre_commands=False,
                output_dir=None,
            ),
            config,
        )


def test_collect_validate_multi_profile(tmp_path, make_config):
    config = make_config(
        tmp_path,
        profiles={
            "good": {"directories": ["src"], "max_tokens": 16000, "split_mode": "by_file"},
            "bad": {"max_tokens": 100},
        },
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    with pytest.raises(SystemExit) as exc_info:
        _cmd_collect_validate(Namespace(), config)
    assert exc_info.value.code == 1


def test_print_collected_with_files(tmp_path):
    import sys
    from io import StringIO

    f = tmp_path / "test.md"
    f.write_text("hello\nworld\n")
    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    print_collected([str(f)])
    sys.stdout = old
    assert "test.md" in out.getvalue()
    assert "3 lines" in out.getvalue()


def test_print_collected_empty():
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    print_collected([])
    sys.stdout = old
    assert "No content collected" in out.getvalue()


def test_write_manifest_basic(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    f = tmp_path / "out" / "chat-c.md"
    f.write_text("content")
    write_manifest(out, [str(f)], {str(f): 50}, {"project_name": "Test"})
    mf = out / "chat-manifest.md"
    assert mf.exists()
    content = mf.read_text()
    assert "Test" in content
    assert "chat-c.md" in content


def test_clean_with_diff_files(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "chat-diff-snap_1.md").write_text("diff")
    (tmp_path / "out" / "chat-diff-v1-to-v2_1.md").write_text("cross")
    _cmd_collect_clean(Namespace(output_dir=None), config)
    assert not (tmp_path / "out" / "chat-diff-snap_1.md").exists()
    assert not (tmp_path / "out" / "chat-diff-v1-to-v2_1.md").exists()


def test_clean_manifest_and_diff_files(tmp_path, make_config):
    config = make_config(tmp_path)
    (tmp_path / "out").mkdir()
    mf = tmp_path / "out" / ".arachna_manifest.json"
    mf.write_text(json.dumps({"files": ["chat-c_1.md", "chat-diff-snap_1.md"]}))
    (tmp_path / "out" / "chat-c_1.md").write_text("collected")
    (tmp_path / "out" / "chat-diff-snap_1.md").write_text("diff")
    _cmd_collect_clean(Namespace(output_dir=None), config)
    assert not (tmp_path / "out" / "chat-c_1.md").exists()
    assert not (tmp_path / "out" / "chat-diff-snap_1.md").exists()
    assert not mf.exists()
