"""Tests for compute_diff — modified, added, deleted, unchanged."""

import json

from arachna.config.profile_config import ProfileConfig
from arachna.snapshot.diff.snapshot_diff import compute_diff, create_snapshot


def _profile(tmp_path):
    return ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
        exclude_patterns=[],
    )


def test_diff_works(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="stream-test", root=root)
    (src / "a.py").write_text("modified")
    diffs = compute_diff(sid, profile, root=root)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1


def test_diff_no_changes(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("unchanged")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="no-changes", root=root)
    diffs = compute_diff(sid, profile, root=root)
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 0


def test_diff_no_changes_no_config(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("unchanged")
    profile = _profile(tmp_path)
    sid = create_snapshot(profile, name="s1", root=tmp_path)
    diffs = compute_diff(sid, profile, root=tmp_path)
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 0


def test_diff_modified_no_config(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("original")
    profile = _profile(tmp_path)
    sid = create_snapshot(profile, name="s2", root=tmp_path)
    (src / "main.py").write_text("modified")
    diffs = compute_diff(sid, profile, root=tmp_path)
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 1
