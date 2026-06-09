"""Test _apply_repo_map_to_sections with to_snapshot_id (cross-snapshot)."""

import json

from arachna.differ import DiffSection
from arachna.gatherer import _apply_repo_map_to_sections
from arachna.watcher import create_snapshot


def _make_profile(directory: str) -> dict:
    return {
        "directories": [directory],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


def test_apply_repo_map_cross_snapshot(tmp_path, monkeypatch):
    """_apply_repo_map_to_sections with to_snapshot_id uses store for both sides."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")

    profile = _make_profile("src")
    sid1 = create_snapshot(profile, name="cross-v1")
    (src / "main.py").write_text("def foo():\n    return 2\n")
    sid2 = create_snapshot(profile, name="cross-v2")

    sections = [
        DiffSection(
            type="modified",
            path="src/main.py",
            content="### src/main.py\n\nREMOVED lines 1:\n    old\n\nADDED lines 1:\n    new\n",
        ),
    ]
    result = _apply_repo_map_to_sections(sections, sid1, sid2, profile)
    assert len(result) == 1
    assert "foo" in result[0].content


def test_apply_repo_map_cross_snapshot_added(tmp_path, monkeypatch):
    """Cross-snapshot repo-map: added file reads from to_snapshot."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "old.py").write_text("def old_func():\n    pass\n")

    profile = _make_profile("src")
    sid1 = create_snapshot(profile, name="cross-add-v1")
    (src / "new.py").write_text("def new_func():\n    pass\n")
    sid2 = create_snapshot(profile, name="cross-add-v2")

    sections = [
        DiffSection(
            type="added",
            path="src/new.py",
            content="### src/new.py\n\nADDED (new file):\n\n```\ndef new_func():\n    pass\n```\n",
        ),
    ]
    result = _apply_repo_map_to_sections(sections, sid1, sid2, profile)
    assert len(result) == 1
    assert "new_func" in result[0].content
