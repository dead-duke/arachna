"""Basic diff tests — inline profiles, no setup_config."""

from arachna.snapshot.snapshots import compute_diff, create_snapshot


def _profile(tmp_path):
    return {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


def test_diff_no_changes(tmp_path):
    import json

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


def test_diff_modified(tmp_path):
    import json

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
