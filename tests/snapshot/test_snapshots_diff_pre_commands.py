from arachna.config.profile_config import ProfileConfig
from arachna.snapshot.snapshots import (
    _diff_pre_commands_line,
    _diff_pre_commands_marker,
    _diff_pre_commands_structural,
    compute_diff,
    create_snapshot,
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
