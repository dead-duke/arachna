"""Tests for compute_diff streaming parameter."""

from arachna.watch.watcher import compute_diff, create_snapshot


def test_streaming_false_works(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="stream-test", root=root)
    (src / "a.py").write_text("modified")
    diffs = compute_diff(sid, profile, streaming=False, root=root)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1


def test_streaming_true_works(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="stream-true-test", root=root)
    (src / "a.py").write_text("modified")
    diffs = compute_diff(sid, profile, streaming=True, root=root)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1


def test_streaming_default_is_false(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="stream-default-test", root=root)
    (src / "a.py").write_text("modified")
    diffs = compute_diff(sid, profile, root=root)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1
