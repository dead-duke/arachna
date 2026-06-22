import sys

import pytest

from arachna.config.profile_config import ProfileConfig
from arachna.snapshot.diff.snapshot_diff import compute_diff, create_snapshot
from arachna.snapshot.diff.snapshot_diff_files import _read_profile_files
from arachna.snapshot.store import load_snapshot


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
        exclude_patterns=[],
        files=[],
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_create_snapshot_includes_profile_files(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    readme = tmp_path / "README.md"
    readme.write_text("# Project")
    profile = make_profile("src", ["*.py"])
    profile.files = [str(readme)]
    sid = create_snapshot(profile, name="with-files", root=root)
    manifest = load_snapshot(sid, root=root)
    filenames = list(manifest["files"].keys())
    assert any("main.py" in f for f in filenames)
    assert any("README.md" in f for f in filenames)


def test_compute_diff_detects_changes_in_profile_files(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("original")
    readme = tmp_path / "README.md"
    readme.write_text("old readme")
    profile = make_profile("src", ["*.py"])
    profile.files = [str(readme)]
    sid = create_snapshot(profile, name="snap1", root=root)
    readme.write_text("new readme")
    diffs = compute_diff(sid, profile, root=root)
    paths = [d.path for d in diffs]
    assert any("README.md" in p for p in paths)


def test_compute_diff_detects_deleted_profile_file(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("unchanged")
    cfg = tmp_path / "config.ini"
    cfg.write_text("old config")
    profile = make_profile("src", ["*.py"])
    profile.files = [str(cfg)]
    sid = create_snapshot(profile, name="snap2", root=root)
    cfg.unlink()
    diffs = compute_diff(sid, profile, root=root)
    types = [d.type for d in diffs]
    assert "deleted" in types


def test_read_profile_files_skips_nonexistent(tmp_path, setup_config):
    root = setup_config()
    (tmp_path / "exists.txt").write_text("hello")
    p = _profile(files=[str(tmp_path / "exists.txt"), str(tmp_path / "ghost.txt")])
    result = _read_profile_files(p, root)
    assert any("exists.txt" in k for k in result)
    assert not any("ghost.txt" in k for k in result)


def test_read_profile_files_skips_unreadable(tmp_path, setup_config):
    if sys.platform == "win32":
        pytest.skip("chmod 0o000 does not prevent reads on Windows")
    root = setup_config()
    secret = tmp_path / "secret.txt"
    secret.write_text("secret")
    import os

    os.chmod(secret, 0o000)
    try:
        p = _profile(files=[str(secret)])
        result = _read_profile_files(p, root)
        assert not any("secret.txt" in k for k in result)
    finally:
        os.chmod(secret, 0o644)
