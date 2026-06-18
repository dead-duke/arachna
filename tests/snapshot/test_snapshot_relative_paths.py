"""Tests for snapshot relative paths (v2.9.2)."""

from arachna.snapshot.snapshots import create_snapshot
from arachna.snapshot.store import load_snapshot


def test_snapshot_relative_paths(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="rel-path-snap", root=root)
    manifest = load_snapshot(sid, root=root)

    for f in manifest["files"]:
        assert f.startswith("src/"), f"Expected relative path starting with src/, got {f}"
        assert not f.startswith("/"), f"Expected relative path, got absolute: {f}"
