"""Coverage for __main__.py — plugin stubs, error paths, edge cases."""

import json
from argparse import Namespace

import pytest

from arachna.__main__ import (
    _cmd_collect_clean,
    _cmd_collect_profile,
    _cmd_collect_validate,
    _cmd_diff,
    _cmd_plugins_install,
    _cmd_plugins_list,
    _cmd_plugins_uninstall,
    _cmd_snapshot_create,
    _cmd_snapshot_delete,
    _cmd_snapshot_info,
    _cmd_snapshot_rename,
    _cmd_snapshot_update,
    _print_collected,
    _write_manifest,
)

# ── Plugin stubs ─────────────────────────────────────────────────


def test_plugins_list():
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_list(Namespace(), {})
    sys.stdout = old
    assert "Plugin system coming in v3.1" in out.getvalue()


def test_plugins_install():
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_install(Namespace(language="javascript"), {})
    sys.stdout = old
    assert "Plugin system coming in v3.1" in out.getvalue()
    assert "javascript" in out.getvalue()


def test_plugins_uninstall():
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_plugins_uninstall(Namespace(language="go"), {})
    sys.stdout = old
    assert "Plugin system coming in v3.1" in out.getvalue()
    assert "go" in out.getvalue()


# ── Snapshot error paths ──────────────────────────────────────────


def test_snapshot_create_no_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    (tmp_path / "src").mkdir()
    with pytest.raises(SystemExit):
        _cmd_snapshot_create(Namespace(name=None, profile="c"), {})


def test_snapshot_create_invalid_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    with pytest.raises(SystemExit):
        _cmd_snapshot_create(Namespace(name="../../etc", profile="c"), {})


def test_snapshot_create_profile_not_found(tmp_path, monkeypatch):
    """Non-existent profile raises SystemExit."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}})
    )
    with pytest.raises(SystemExit):
        _cmd_snapshot_create(Namespace(name="test", profile="nonexistent"), {})


def test_snapshot_delete_invalid_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    with pytest.raises(SystemExit):
        _cmd_snapshot_delete(Namespace(id="../../etc"), {})


def test_snapshot_info_invalid_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    with pytest.raises(SystemExit):
        _cmd_snapshot_info(Namespace(id="../../etc", profile_only=False, stats_only=False), {})


def test_snapshot_info_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    with pytest.raises(SystemExit):
        _cmd_snapshot_info(Namespace(id="nonexist", profile_only=False, stats_only=False), {})


def test_snapshot_rename_invalid_old(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    with pytest.raises(SystemExit):
        _cmd_snapshot_rename(Namespace(old="../../etc", new="ok"), {})


def test_snapshot_rename_invalid_new(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    with pytest.raises(SystemExit):
        _cmd_snapshot_rename(Namespace(old="ok", new="../../etc"), {})


def test_snapshot_update_invalid_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    with pytest.raises(SystemExit):
        _cmd_snapshot_update(Namespace(id="../../etc", profile=None), {})


def test_snapshot_update_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    with pytest.raises(SystemExit):
        _cmd_snapshot_update(Namespace(id="nonexist", profile=None), {})


def test_snapshot_update_profile_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}})
    )
    from arachna.store import create_snapshot as store_create

    store_create({"a.py": "x"}, name="test-snap")
    with pytest.raises(SystemExit):
        _cmd_snapshot_update(Namespace(id="test-snap", profile="nonexistent"), {})


# ── Diff error paths ──────────────────────────────────────────────


def test_diff_all_and_from_conflict(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
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
            {},
        )


def test_diff_no_snapshots(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
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
            {},
        )


def test_diff_profile_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}})
    )
    from arachna.store import create_snapshot as store_create

    store_create({"a.py": "x"}, name="test-snap")
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
            {},
        )


def test_diff_all_profile_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}})
    )
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
            {},
        )


# ── Collect error paths ───────────────────────────────────────────


def test_collect_profile_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}})
    )
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
            {},
        )


def test_collect_validate_multi_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "good": {"directories": ["src"], "max_tokens": 16000, "split_mode": "by_file"},
                    "bad": {"max_tokens": 100},
                }
            }
        )
    )
    with pytest.raises(SystemExit) as exc_info:
        _cmd_collect_validate(Namespace(), json.loads((tmp_path / ".arachna.json").read_text()))
    assert exc_info.value.code == 1


# ── Print collected / write manifest ──────────────────────────────


def test_print_collected_with_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "test.md"
    f.write_text("hello\nworld\n")

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _print_collected([str(f)])
    sys.stdout = old
    assert "test.md" in out.getvalue()
    assert "3 lines" in out.getvalue()


def test_print_collected_empty():
    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _print_collected([])
    sys.stdout = old
    assert "No content collected" in out.getvalue()


def test_write_manifest_basic(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    f = tmp_path / "out" / "chat-c.md"
    f.write_text("content")

    _write_manifest(out, [str(f)], {str(f): 50}, {"project_name": "Test"})

    mf = out / "chat-manifest.md"
    assert mf.exists()
    content = mf.read_text()
    assert "Test" in content
    assert "chat-c.md" in content


# ── Clean edge cases ──────────────────────────────────────────────


def test_clean_with_diff_files(tmp_path, monkeypatch):
    """Clean removes diff files via glob patterns — files in cwd (default output_dir='.')."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    # _parse_output_dir(Namespace(output_dir=None), {}) returns "." = tmp_path
    (tmp_path / "chat-diff-snap_1.md").write_text("diff")
    (tmp_path / "chat-diff-v1-to-v2_1.md").write_text("cross")

    _cmd_collect_clean(Namespace(output_dir=None), {})

    assert not (tmp_path / "chat-diff-snap_1.md").exists()
    assert not (tmp_path / "chat-diff-v1-to-v2_1.md").exists()


def test_clean_manifest_and_diff_files(tmp_path, monkeypatch):
    """Clean with manifest removes manifest-tracked files AND diff files."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    # _parse_output_dir returns "." = tmp_path
    mf = tmp_path / ".arachna_manifest.json"
    mf.write_text(json.dumps({"files": ["chat-c_1.md", "chat-diff-snap_1.md"]}))
    (tmp_path / "chat-c_1.md").write_text("collected")
    (tmp_path / "chat-diff-snap_1.md").write_text("diff")

    _cmd_collect_clean(Namespace(output_dir=None), {})

    assert not (tmp_path / "chat-c_1.md").exists()
    assert not (tmp_path / "chat-diff-snap_1.md").exists()
    assert not mf.exists()
