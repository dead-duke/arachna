"""Tests for compute_diff."""

from arachna.snapshot.diff.snapshot_diff import compute_diff, create_snapshot


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
