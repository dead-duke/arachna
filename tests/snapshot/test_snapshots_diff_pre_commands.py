"""Tests for diff of pre_commands — line diff, marker diff, structural diff, integration."""

from arachna.config.profile_config import ProfileConfig
from arachna.domain.api_types import DiffSection
from arachna.snapshot.diff.snapshot_diff import (
    _format_summary_header,
    _group_diff_sections,
    compute_diff,
    create_snapshot,
)
from arachna.snapshot.diff.snapshot_diff_commands import (
    _diff_pre_commands_line,
    _diff_pre_commands_marker,
    _diff_pre_commands_structural,
)


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
        exclude_patterns=[],
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_diff_pre_commands_line_added_only():
    old = "src/main.py\nsrc/utils.py\n"
    new = "src/main.py\nsrc/utils.py\nsrc/new.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "+ src/new.py" in result
    assert "- " not in result


def test_diff_pre_commands_line_deleted_only():
    old = "src/main.py\nsrc/utils.py\nsrc/old.py\n"
    new = "src/main.py\nsrc/utils.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "- src/old.py" in result
    assert "+ " not in result


def test_diff_pre_commands_line_mixed():
    old = "src/main.py\nsrc/old.py\n"
    new = "src/main.py\nsrc/new.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "- src/old.py" in result
    assert "+ src/new.py" in result


def test_diff_pre_commands_line_unchanged():
    old = "src/main.py\nsrc/utils.py\n"
    new = "src/main.py\nsrc/utils.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert result == ""


def test_diff_pre_commands_line_empty_old():
    old = ""
    new = "src/main.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "+ src/main.py" in result


def test_diff_pre_commands_line_empty_new():
    old = "src/main.py\n"
    new = ""
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "- src/main.py" in result


def test_diff_pre_commands_marker_modified_section():
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: abc ===\nold message\n\n=== COMMIT: def ===\nsame\n"
    new = "=== COMMIT: abc ===\nnew message\n\n=== COMMIT: def ===\nsame\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "REMOVED" in result or "ADDED" in result


def test_diff_pre_commands_marker_added_section():
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: abc ===\nmessage\n"
    new = "=== COMMIT: abc ===\nmessage\n\n=== COMMIT: def ===\nnew\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "ADDED (new file)" in result or "section 2" in result


def test_diff_pre_commands_marker_deleted_section():
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: abc ===\nmsg1\n\n=== COMMIT: def ===\nmsg2\n"
    new = "=== COMMIT: abc ===\nmsg1\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "DELETED" in result


def test_diff_pre_commands_marker_unchanged():
    marker = "\n=== COMMIT:"
    content = "=== COMMIT: abc ===\nsame\n"
    result = _diff_pre_commands_marker(content, content, "pre: git log", marker, "markdown")
    assert result == ""


def test_diff_pre_commands_structural_tree_line_diff():
    old = "src/main.py\nsrc/old.py\n"
    new = "src/main.py\nsrc/new.py\n"
    result = _diff_pre_commands_structural(old, new, "pre: tree src", "tree src", "markdown")
    assert "+ src/new.py" in result
    assert "- src/old.py" in result


def test_diff_pre_commands_structural_git_tag_line_diff():
    old = "v1.0.0\nv1.1.0\n"
    new = "v1.0.0\nv1.1.0\nv1.2.0\n"
    result = _diff_pre_commands_structural(
        old, new, "pre: git tag", "git tag --sort=-creatordate", "markdown"
    )
    assert "+ v1.2.0" in result


def test_diff_pre_commands_structural_git_log_marker_diff():
    cmd = "git log --reverse --format='=== COMMIT: %h ===%nTITLE: %s'"
    old = "=== COMMIT: abc ===\nold title\n"
    new = "=== COMMIT: abc ===\nnew title\n"
    result = _diff_pre_commands_structural(old, new, "pre: git log", cmd, "markdown")
    assert "REMOVED" in result or "ADDED" in result


def test_diff_pre_commands_structural_unknown_fallback():
    old = "line1\nline2\nline3\n"
    new = "line1\nchanged\nline3\n"
    result = _diff_pre_commands_structural(old, new, "pre: unknown", "unknown_cmd arg", "markdown")
    assert "REMOVED" in result or "ADDED" in result


def test_compute_diff_pre_commands_tree_changed(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    p1 = _profile(pre_commands=["echo 'file1.py'"])
    sid = create_snapshot(p1, name="tree-int-snap", root=tmp_path)
    p2 = _profile(pre_commands=["echo 'file1.py\nfile2.py'"])
    diffs = compute_diff(sid, p2, root=tmp_path)
    pre_diffs = [d for d in diffs if d.path and d.path.startswith("pre:")]
    assert len(pre_diffs) >= 1


# From test_snapshots_isolated.py


def test_format_summary_header_all_types():
    stats = {"renamed": 2, "moved": 1, "modified": 5, "added": 3, "deleted": 1}
    header = _format_summary_header(stats, "snap1", "snap2")
    assert "Changes from snap1 to snap2" in header
    assert "2 renamed" in header
    assert "1 moved" in header
    assert "5 modified" in header
    assert "3 added" in header
    assert "1 deleted" in header


def test_format_summary_header_no_changes():
    stats = {"renamed": 0, "moved": 0, "modified": 0, "added": 0, "deleted": 0}
    header = _format_summary_header(stats, "snap1", None)
    assert "No changes" in header


def test_group_diff_sections_order():
    sections = [
        DiffSection(type="deleted", path="d.py", content="[DELETED]"),
        DiffSection(type="modified", path="a.py", content="diff"),
        DiffSection(type="added", path="c.py", content="new"),
        DiffSection(type="modified", path="b.py", content="diff2"),
    ]
    grouped = _group_diff_sections(sections, "snap1", "current")
    types = [s.type for s in grouped if s.type != "header"]
    assert types[0] == "modified"
    assert types[1] == "modified"
    assert "added" in types
    assert "deleted" in types


def test_group_diff_sections_empty():
    assert _group_diff_sections([], "snap1", None) == []


def test_diff_pre_commands_line_added():
    old = "src/main.py\n"
    new = "src/main.py\nsrc/new.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "+ src/new.py" in result


def test_diff_pre_commands_line_deleted():
    old = "src/main.py\nsrc/old.py\n"
    new = "src/main.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "- src/old.py" in result


def test_diff_pre_commands_line_unchanged_isolated():
    result = _diff_pre_commands_line("same\n", "same\n", "pre: test")
    assert result == ""


def test_diff_pre_commands_marker_modified_isolated():
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: abc ===\nold\n"
    new = "=== COMMIT: abc ===\nnew\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "REMOVED" in result or "ADDED" in result


def test_diff_pre_commands_marker_added_isolated():
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: a ===\nmsg\n"
    new = "=== COMMIT: a ===\nmsg\n\n=== COMMIT: b ===\nnew\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "section 2" in result


def test_diff_pre_commands_marker_deleted_isolated():
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: a ===\n1\n\n=== COMMIT: b ===\n2\n"
    new = "=== COMMIT: a ===\n1\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "DELETED" in result
