"""Tests for snapshot relative paths (v2.9.2)."""

import json

from arachna.store import load_snapshot
from arachna.watcher import _rel_path, create_snapshot


def _make_profile(directory: str, patterns=None) -> dict:
    return {
        "directories": [directory],
        "patterns": patterns or ["*"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


def _setup_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )


def test_snapshot_relative_paths(tmp_path, monkeypatch):
    """Snapshot manifest stores paths relative to project root."""
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = _make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="rel-path-snap")
    manifest = load_snapshot(sid)

    for f in manifest["files"]:
        assert f.startswith("src/"), f"Expected relative path starting with src/, got {f}"
        assert not f.startswith("/"), f"Expected relative path, got absolute: {f}"
        assert "private" not in f, f"Expected relative path, got absolute: {f}"


def test_rel_path_fallback_no_config(tmp_path, monkeypatch):
    """_rel_path falls back to normalized absolute when no config."""
    monkeypatch.chdir(tmp_path)
    f = tmp_path / "test.txt"
    f.write_text("hello")
    path = _rel_path(f.resolve())
    assert "test.txt" in path
