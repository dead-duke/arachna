"""Tests for compute_diff streaming parameter."""

from arachna.watcher import compute_diff, create_snapshot


def test_streaming_false_works(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="stream-test")
    (src / "a.py").write_text("modified")
    diffs = compute_diff(sid, profile, streaming=False)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1


def test_streaming_true_works(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="stream-true-test")
    (src / "a.py").write_text("modified")
    diffs = compute_diff(sid, profile, streaming=True)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1


def test_streaming_default_is_false(tmp_path, setup_config, make_profile):
    setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("original")
    profile = make_profile("src", ["*.py"])
    sid = create_snapshot(profile, name="stream-default-test")
    (src / "a.py").write_text("modified")
    diffs = compute_diff(sid, profile)
    content_diffs = [d for d in diffs if d.type == "modified" and d.path]
    assert len(content_diffs) == 1
