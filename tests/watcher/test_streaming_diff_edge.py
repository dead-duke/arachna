"""Edge cases for compute_diff streaming=True."""

from arachna.watcher import compute_diff, create_snapshot


def _profile(tmp_path):
    return {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


def test_streaming_true_no_changes(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        __import__("json").dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("unchanged")
    profile = _profile(tmp_path)
    sid = create_snapshot(profile, name="stream-unchanged", root=tmp_path)
    diffs = compute_diff(sid, profile, streaming=True, root=tmp_path)
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 0


def test_streaming_false_no_changes(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        __import__("json").dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("unchanged")
    profile = _profile(tmp_path)
    sid = create_snapshot(profile, name="stream-false", root=tmp_path)
    diffs = compute_diff(sid, profile, streaming=False, root=tmp_path)
    content_diffs = [d for d in diffs if d.path]
    assert len(content_diffs) == 0


def test_streaming_same_result(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        __import__("json").dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("original")
    profile = _profile(tmp_path)
    sid = create_snapshot(profile, name="stream-cmp", root=tmp_path)
    (src / "main.py").write_text("modified")
    diffs_true = compute_diff(sid, profile, streaming=True, root=tmp_path)
    diffs_false = compute_diff(sid, profile, streaming=False, root=tmp_path)
    assert len(diffs_true) == len(diffs_false)
