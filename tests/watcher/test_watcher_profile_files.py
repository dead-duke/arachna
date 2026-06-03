"""Tests for watcher profile files support (v1.6.2)."""

from arachna.store import load_snapshot
from arachna.watcher import _read_profile_files, compute_diff, create_snapshot


def _make_profile(directory: str, patterns=None, files=None) -> dict:
    return {
        "directories": [directory],
        "patterns": patterns or ["*"],
        "files": files or [],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


def test_create_snapshot_includes_profile_files(tmp_path, monkeypatch):
    """create_snapshot includes explicit files from profile.files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    readme = tmp_path / "README.md"
    readme.write_text("# Project")

    profile = _make_profile("src", ["*.py"], files=["README.md"])
    sid = create_snapshot(profile, name="with-files")

    manifest = load_snapshot(sid)
    filenames = list(manifest["files"].keys())
    assert "src/main.py" in filenames
    assert "README.md" in filenames


def test_compute_diff_detects_changes_in_profile_files(tmp_path, monkeypatch):
    """compute_diff detects modifications in explicit profile files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("original")
    readme = tmp_path / "README.md"
    readme.write_text("old readme")

    profile = _make_profile("src", ["*.py"], files=["README.md"])
    sid = create_snapshot(profile, name="snap1")

    readme.write_text("new readme")

    diffs = compute_diff(sid, profile)
    paths = [d.path for d in diffs]
    assert "README.md" in paths


def test_compute_diff_detects_deleted_profile_file(tmp_path, monkeypatch):
    """compute_diff detects when explicit profile file is deleted."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("unchanged")
    cfg = tmp_path / "config.ini"
    cfg.write_text("old config")

    profile = _make_profile("src", ["*.py"], files=["config.ini"])
    sid = create_snapshot(profile, name="snap1")

    cfg.unlink()

    diffs = compute_diff(sid, profile)
    types = [d.type for d in diffs]
    assert "deleted" in types


def test_read_profile_files_skips_nonexistent(tmp_path, monkeypatch):
    """_read_profile_files skips files that don't exist."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "exists.txt").write_text("hello")

    profile = {"files": ["exists.txt", "ghost.txt"]}
    result = _read_profile_files(profile)
    assert "exists.txt" in result
    assert "ghost.txt" not in result


def test_read_profile_files_skips_unreadable(tmp_path, monkeypatch):
    """_read_profile_files skips files that raise OSError on read."""
    import sys

    import pytest

    if sys.platform == "win32":
        pytest.skip("chmod 0o000 does not prevent reads on Windows")

    monkeypatch.chdir(tmp_path)
    secret = tmp_path / "secret.txt"
    secret.write_text("secret")
    import os

    os.chmod(secret, 0o000)
    try:
        profile = {"files": ["secret.txt"]}
        result = _read_profile_files(profile)
        assert "secret.txt" not in result
    finally:
        os.chmod(secret, 0o644)
