"""Tests for snapshots — create, diff, flat, grouped, edge cases."""

import os
import sys
from pathlib import Path

import pytest

from arachna.config.profile_config import ProfileConfig
from arachna.snapshot.diff.snapshot_diff import compute_diff, create_snapshot
from arachna.snapshot.diff.snapshot_diff_files import _path_matches_profile
from arachna.snapshot.diff.snapshot_diff_helpers import _normalize_path, _rel_path
from arachna.snapshot.store import load_snapshot


def _profile(dirs=None, pats=None):
    return ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=dirs or ["src"],
        patterns=pats or ["*.py"],
        use_gitignore=False,
    )


def test_create_snapshot_returns_id(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="test-snap", root=root)
    assert sid == "test-snap"


def test_create_snapshot_stores_files(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "utils.py").write_text("def foo(): pass")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="files-snap", root=root)
    manifest = load_snapshot(sid, root=root)
    assert len(manifest["files"]) == 2
    assert any("main.py" in f for f in manifest["files"])
    assert any("utils.py" in f for f in manifest["files"])


def test_compute_diff_modified(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="snap1", root=root)
    (src / "a.py").write_text("modified")
    diffs = compute_diff(sid, profile, root=root)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1
    assert content_diffs[0].type == "modified"
    assert content_diffs[0].path == "src/a.py"


def test_compute_diff_added(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("existing")
    profile = make_profile("src", ["*.py"])
    create_snapshot(profile, name="snap2", root=root)
    (src / "b.py").write_text("new file")
    diffs = compute_diff("snap2", profile, root=root)
    content_diffs = [d for d in diffs if d.type == "added" and d.path]
    assert len(content_diffs) == 1
    assert content_diffs[0].type == "added"
    assert content_diffs[0].path == "src/b.py"


def test_compute_diff_deleted(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("to be deleted")
    profile = make_profile("src", ["*.py"])
    create_snapshot(profile, name="snap3", root=root)
    (src / "a.py").unlink()
    diffs = compute_diff("snap3", profile, root=root)
    content_diffs = [d for d in diffs if d.type == "deleted" and d.path]
    assert len(content_diffs) == 1
    assert content_diffs[0].type == "deleted"
    assert content_diffs[0].path == "src/a.py"


def test_compute_diff_unchanged(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("unchanged")
    profile = make_profile("src", ["*.py"])
    create_snapshot(profile, name="snap4", root=root)
    diffs = compute_diff("snap4", profile, root=root)
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 0


def test_compute_diff_profile_change_ignored(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("keep")
    (src / "b.py").write_text("remove from profile")
    profile_both = make_profile("src", ["*.py"])
    create_snapshot(profile_both, name="snap5", root=root)
    profile_a = make_profile("src", ["a.py"])
    diffs = compute_diff("snap5", profile_a, root=root)
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 0


def test_compute_diff_flat_mode(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    create_snapshot(profile, name="snap6", root=root)
    (src / "a.py").write_text("modified")
    diffs = compute_diff("snap6", profile, flat=True, root=root)
    assert len(diffs) == 1
    assert diffs[0].type == "modified"
    assert diffs[0].path == "src/a.py"


def test_compute_diff_grouped_has_header(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    create_snapshot(profile, name="snap7", root=root)
    (src / "a.py").write_text("modified")
    diffs = compute_diff("snap7", profile, root=root)
    headers = [d for d in diffs if d.type == "header"]
    assert len(headers) == 1
    assert "Changes from snap7 to current" in headers[0].content
    assert "1 modified" in headers[0].content


def test_compute_diff_grouped_order(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "mod.py").write_text("original")
    (src / "gone.py").write_text("delete me")
    profile = make_profile("src", ["*.py"])
    create_snapshot(profile, name="snap8", root=root)
    (src / "mod.py").write_text("changed")
    (src / "gone.py").unlink()
    (src / "new.py").write_text("new file")
    diffs = compute_diff("snap8", profile, root=root)
    types_in_order = [d.type for d in diffs if d.type and d.type != "header"]
    assert "modified" in types_in_order
    assert "added" in types_in_order
    assert "deleted" in types_in_order


# Edge cases


def test_create_snapshot_skip_unreadable(tmp_path, setup_config, make_profile):
    if sys.platform == "win32":
        pytest.skip("chmod 0o000 does not prevent reads on Windows")
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "good.py").write_text("print('ok')")
    bad = src / "bad.py"
    bad.write_text("secret")
    os.chmod(bad, 0o000)
    try:
        profile = make_profile("src", ["*.py"])
        sid = create_snapshot(profile, name="skip-unreadable", root=root)
        manifest = load_snapshot(sid, root=root)
        filenames = list(manifest["files"].keys())
        assert any("good.py" in f for f in filenames)
        assert not any("bad.py" in f for f in filenames)
    finally:
        os.chmod(bad, 0o644)


def test_create_snapshot_skip_binary(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "good.py").write_text("print('ok')")
    (src / "data.bin").write_bytes(b"\x80\x81\x82")
    profile = make_profile("src", ["*"])
    sid = create_snapshot(profile, name="skip-binary", root=root)
    manifest = load_snapshot(sid, root=root)
    filenames = list(manifest["files"].keys())
    assert any("good.py" in f for f in filenames)
    assert not any("data.bin" in f for f in filenames)


def test_create_snapshot_empty_dir(tmp_path, setup_config, make_profile):
    root = setup_config()
    (tmp_path / "empty").mkdir()
    profile = make_profile("empty", ["*.py"])
    sid = create_snapshot(profile, name="empty-dir", root=root)
    manifest = load_snapshot(sid, root=root)
    assert manifest["files"] == {}


def test_compute_diff_file_outside_root(tmp_path, setup_config):
    root = setup_config()
    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*"],
        use_gitignore=False,
    )
    assert not _path_matches_profile("/etc/passwd", p, root)


def test_path_matches_profile_nested(tmp_path, setup_config):
    root = setup_config()
    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
    )
    assert _path_matches_profile("src/main.py", p, root)
    assert _path_matches_profile("src/sub/nested.py", p, root)
    assert not _path_matches_profile("tests/test.py", p, root)
    assert not _path_matches_profile("README.md", p, root)


def test_path_matches_profile_wrong_pattern(tmp_path, setup_config):
    root = setup_config()
    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.rs"],
        use_gitignore=False,
    )
    assert not _path_matches_profile("src/main.py", p, root)


def test_rel_path_outside_root(tmp_path):
    result = _rel_path(Path("/etc/passwd"), tmp_path)
    assert result == "/etc/passwd"


def test_rel_path_inside_root(tmp_path):
    f = tmp_path / "src" / "main.py"
    f.parent.mkdir()
    f.write_text("code")
    result = _rel_path(f.resolve(), tmp_path)
    assert result == "src/main.py"


def test_normalize_path_backslashes():
    assert _normalize_path("src\\main.py") == "src/main.py"
    assert _normalize_path("src\\\\nested\\file.py") == "src/nested/file.py"
