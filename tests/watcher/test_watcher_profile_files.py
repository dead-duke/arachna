"""Tests for watcher profile files support (v1.6.2)."""

import sys

import pytest

from arachna.store import load_snapshot
from arachna.watcher import _read_profile_files, compute_diff, create_snapshot


def test_create_snapshot_includes_profile_files(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    readme = tmp_path / "README.md"
    readme.write_text("# Project")
    profile = make_profile("src", ["*.py"])
    profile["files"] = ["README.md"]
    sid = create_snapshot(profile, name="with-files")
    manifest = load_snapshot(sid)
    filenames = list(manifest["files"].keys())
    assert any("main.py" in f for f in filenames)
    assert any("README.md" in f for f in filenames)


def test_compute_diff_detects_changes_in_profile_files(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("original")
    readme = tmp_path / "README.md"
    readme.write_text("old readme")
    profile = make_profile("src", ["*.py"])
    profile["files"] = ["README.md"]
    sid = create_snapshot(profile, name="snap1")
    readme.write_text("new readme")
    diffs = compute_diff(sid, profile)
    paths = [d.path for d in diffs]
    assert "README.md" in paths


def test_compute_diff_detects_deleted_profile_file(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("unchanged")
    cfg = tmp_path / "config.ini"
    cfg.write_text("old config")
    profile = make_profile("src", ["*.py"])
    profile["files"] = ["config.ini"]
    sid = create_snapshot(profile, name="snap1")
    cfg.unlink()
    diffs = compute_diff(sid, profile)
    types = [d.type for d in diffs]
    assert "deleted" in types


def test_read_profile_files_skips_nonexistent(tmp_path, setup_config):
    setup_config()
    (tmp_path / "exists.txt").write_text("hello")
    profile = {"files": ["exists.txt", "ghost.txt"]}
    result = _read_profile_files(profile)
    assert any("exists.txt" in k for k in result)
    assert not any("ghost.txt" in k for k in result)


def test_read_profile_files_skips_unreadable(tmp_path, setup_config):
    if sys.platform == "win32":
        pytest.skip("chmod 0o000 does not prevent reads on Windows")
    setup_config()
    secret = tmp_path / "secret.txt"
    secret.write_text("secret")
    import os

    os.chmod(secret, 0o000)
    try:
        profile = {"files": ["secret.txt"]}
        result = _read_profile_files(profile)
        assert not any("secret.txt" in k for k in result)
    finally:
        os.chmod(secret, 0o644)
