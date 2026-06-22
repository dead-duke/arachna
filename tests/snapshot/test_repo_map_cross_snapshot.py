"""Test _apply_repo_map_to_sections with to_snapshot_id (cross-snapshot)."""

from arachna.domain.api_types import DiffSection
from arachna.snapshot.diff.snapshot_diff import create_snapshot
from arachna.snapshot.diff.snapshot_diff_repo_map import apply_repo_map_to_sections


def test_apply_repo_map_cross_snapshot(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
    profile = make_profile("src", ["*.py"])
    sid1 = create_snapshot(profile, name="cross-v1", root=root)
    (src / "main.py").write_text("def foo():\n    return 2\n")
    sid2 = create_snapshot(profile, name="cross-v2", root=root)
    sections = [
        DiffSection(
            type="modified",
            path="src/main.py",
            content="### src/main.py\n\nREMOVED lines 1:\n    old\n\nADDED lines 1:\n    new\n",
        ),
    ]
    result = apply_repo_map_to_sections(sections, sid1, sid2, root=root)
    assert len(result) == 1
    assert "foo" in result[0].content


def test_apply_repo_map_cross_snapshot_added(tmp_path, setup_config, make_profile):
    root = setup_config()
    src = tmp_path / "src"
    src.mkdir()
    (src / "old.py").write_text("def old_func():\n    pass\n")
    profile = make_profile("src", ["*.py"])
    sid1 = create_snapshot(profile, name="cross-add-v1", root=root)
    (src / "new.py").write_text("def new_func():\n    pass\n")
    sid2 = create_snapshot(profile, name="cross-add-v2", root=root)
    sections = [
        DiffSection(
            type="added",
            path="src/new.py",
            content="### src/new.py\n\nADDED (new file):\n\n```\ndef new_func():\n    pass\n```\n",
        ),
    ]
    result = apply_repo_map_to_sections(sections, sid1, sid2, root=root)
    assert len(result) == 1
    assert "new_func" in result[0].content
