"""Edge case tests for watcher.py."""

import sys

import pytest


def test_create_snapshot_skip_unreadable(tmp_path, setup_config, make_profile):
    if sys.platform == "win32":
        pytest.skip("chmod 0o000 does not prevent reads on Windows")
    root = setup_config()
    from arachna.watch.watcher import create_snapshot

    src = tmp_path / "src"
    src.mkdir()
    (src / "good.py").write_text("print('ok')")
    bad = src / "bad.py"
    bad.write_text("secret")
    import os

    os.chmod(bad, 0o000)
    try:
        profile = make_profile("src", ["*.py"])
        sid = create_snapshot(profile, name="skip-unreadable", root=root)
        from arachna.watch.store import load_snapshot

        manifest = load_snapshot(sid, root=root)
        filenames = list(manifest["files"].keys())
        assert any("good.py" in f for f in filenames)
        assert not any("bad.py" in f for f in filenames)
    finally:
        os.chmod(bad, 0o644)


def test_create_snapshot_skip_binary(tmp_path, setup_config, make_profile):
    root = setup_config()
    from arachna.watch.watcher import create_snapshot

    src = tmp_path / "src"
    src.mkdir()
    (src / "good.py").write_text("print('ok')")
    (src / "data.bin").write_bytes(b"\x80\x81\x82")
    profile = make_profile("src", ["*"])
    sid = create_snapshot(profile, name="skip-binary", root=root)
    from arachna.watch.store import load_snapshot

    manifest = load_snapshot(sid, root=root)
    filenames = list(manifest["files"].keys())
    assert any("good.py" in f for f in filenames)
    assert not any("data.bin" in f for f in filenames)


def test_create_snapshot_empty_dir(tmp_path, setup_config, make_profile):
    root = setup_config()
    from arachna.watch.watcher import create_snapshot

    (tmp_path / "empty").mkdir()
    profile = make_profile("empty", ["*.py"])
    sid = create_snapshot(profile, name="empty-dir", root=root)
    from arachna.watch.store import load_snapshot

    manifest = load_snapshot(sid, root=root)
    assert manifest["files"] == {}


def test_compute_diff_file_outside_root(tmp_path, setup_config):
    root = setup_config()
    from arachna.watch.watcher import _path_matches_profile

    assert not _path_matches_profile(
        "/etc/passwd", {"directories": ["src"], "patterns": ["*"]}, root
    )


def test_path_matches_profile_nested(tmp_path, setup_config):
    root = setup_config()
    from arachna.watch.watcher import _path_matches_profile

    profile = {"directories": ["src"], "patterns": ["*.py"]}
    assert _path_matches_profile("src/main.py", profile, root)
    assert _path_matches_profile("src/sub/nested.py", profile, root)
    assert not _path_matches_profile("tests/test.py", profile, root)
    assert not _path_matches_profile("README.md", profile, root)


def test_path_matches_profile_wrong_pattern(tmp_path, setup_config):
    root = setup_config()
    from arachna.watch.watcher import _path_matches_profile

    profile = {"directories": ["src"], "patterns": ["*.rs"]}
    assert not _path_matches_profile("src/main.py", profile, root)


def test_rel_path_outside_root(tmp_path):
    """_rel_path with path outside root falls back to normalized absolute path."""
    from pathlib import Path

    from arachna.watch.watcher_diff import _rel_path

    result = _rel_path(Path("/etc/passwd"), tmp_path)
    assert result == "/etc/passwd"


def test_rel_path_inside_root(tmp_path):
    """_rel_path with path inside root returns relative path."""
    from arachna.watch.watcher_diff import _rel_path

    f = tmp_path / "src" / "main.py"
    f.parent.mkdir()
    f.write_text("code")
    result = _rel_path(f.resolve(), tmp_path)
    assert result == "src/main.py"


def test_normalize_path_backslashes():
    """_normalize_path converts backslashes to forward slashes."""
    from arachna.watch.watcher_diff import _normalize_path

    assert _normalize_path("src\\main.py") == "src/main.py"
    assert _normalize_path("src\\\\nested\\file.py") == "src/nested/file.py"
