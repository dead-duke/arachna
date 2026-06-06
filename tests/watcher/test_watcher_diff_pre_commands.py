"""Tests for _diff_pre_commands_* helpers in watcher.py (v2.3.0 coverage)."""

from arachna.watcher import (
    _diff_pre_commands_line,
    _diff_pre_commands_marker,
    _diff_pre_commands_structural,
    compute_diff,
    create_snapshot,
)


def _make_file_profile(directory: str, patterns=None) -> dict:
    return {
        "directories": [directory],
        "patterns": patterns or ["*"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


# ── _diff_pre_commands_line ──────────────────────────────────────


def test_diff_pre_commands_line_added_only():
    """New lines detected as added."""
    old = "src/main.py\nsrc/utils.py\n"
    new = "src/main.py\nsrc/utils.py\nsrc/new.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "+ src/new.py" in result
    assert "- " not in result


def test_diff_pre_commands_line_deleted_only():
    """Removed lines detected as deleted."""
    old = "src/main.py\nsrc/utils.py\nsrc/old.py\n"
    new = "src/main.py\nsrc/utils.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "- src/old.py" in result
    assert "+ " not in result


def test_diff_pre_commands_line_mixed():
    """Both added and deleted lines."""
    old = "src/main.py\nsrc/old.py\n"
    new = "src/main.py\nsrc/new.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "- src/old.py" in result
    assert "+ src/new.py" in result


def test_diff_pre_commands_line_unchanged():
    """No changes returns empty string."""
    old = "src/main.py\nsrc/utils.py\n"
    new = "src/main.py\nsrc/utils.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert result == ""


def test_diff_pre_commands_line_empty_old():
    """All lines are new when old is empty."""
    old = ""
    new = "src/main.py\n"
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "+ src/main.py" in result


def test_diff_pre_commands_line_empty_new():
    """All lines are deleted when new is empty."""
    old = "src/main.py\n"
    new = ""
    result = _diff_pre_commands_line(old, new, "pre: tree src")
    assert "- src/main.py" in result


# ── _diff_pre_commands_marker ────────────────────────────────────


def test_diff_pre_commands_marker_modified_section():
    """Section content change detected."""
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: abc ===\nold message\n\n=== COMMIT: def ===\nsame\n"
    new = "=== COMMIT: abc ===\nnew message\n\n=== COMMIT: def ===\nsame\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "REMOVED" in result or "ADDED" in result


def test_diff_pre_commands_marker_added_section():
    """New section added at end."""
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: abc ===\nmessage\n"
    new = "=== COMMIT: abc ===\nmessage\n\n=== COMMIT: def ===\nnew\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "ADDED (new file)" in result or "section 2" in result


def test_diff_pre_commands_marker_deleted_section():
    """Section removed."""
    marker = "\n=== COMMIT:"
    old = "=== COMMIT: abc ===\nmsg1\n\n=== COMMIT: def ===\nmsg2\n"
    new = "=== COMMIT: abc ===\nmsg1\n"
    result = _diff_pre_commands_marker(old, new, "pre: git log", marker, "markdown")
    assert "DELETED" in result


def test_diff_pre_commands_marker_unchanged():
    """Same sections produce empty result."""
    marker = "\n=== COMMIT:"
    content = "=== COMMIT: abc ===\nsame\n"
    result = _diff_pre_commands_marker(content, content, "pre: git log", marker, "markdown")
    assert result == ""


# ── _diff_pre_commands_structural ────────────────────────────────


def test_diff_pre_commands_structural_tree_line_diff():
    """tree command uses line-based diff."""
    old = "src/main.py\nsrc/old.py\n"
    new = "src/main.py\nsrc/new.py\n"
    result = _diff_pre_commands_structural(old, new, "pre: tree src", "tree src")
    assert "- src/old.py" in result
    assert "+ src/new.py" in result


def test_diff_pre_commands_structural_git_tag_line_diff():
    """git tag uses line-based diff."""
    old = "v1.0.0\nv1.1.0\n"
    new = "v1.0.0\nv1.1.0\nv1.2.0\n"
    result = _diff_pre_commands_structural(old, new, "pre: git tag", "git tag --sort=-creatordate")
    assert "+ v1.2.0" in result


def test_diff_pre_commands_structural_git_log_marker_diff():
    """git log uses marker-based diff."""
    cmd = "git log --reverse --format='=== COMMIT: %h ===%nTITLE: %s'"
    old = "=== COMMIT: abc ===\nold title\n"
    new = "=== COMMIT: abc ===\nnew title\n"
    result = _diff_pre_commands_structural(old, new, "pre: git log", cmd)
    assert "REMOVED" in result or "ADDED" in result


def test_diff_pre_commands_structural_unknown_command_fallback():
    """Unknown command falls back to text diff."""
    old = "line1\nline2\nline3\n"
    new = "line1\nchanged\nline3\n"
    result = _diff_pre_commands_structural(old, new, "pre: unknown", "unknown_cmd arg")
    assert "REMOVED" in result or "ADDED" in result


# ── Integration: structural pre_commands diff through compute_diff ─


def test_compute_diff_pre_commands_tree_changed(tmp_path, monkeypatch):
    """compute_diff uses structural diff for tree pre_commands."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile1 = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo 'file1.py'"],
    }
    sid = create_snapshot(profile1, name="tree-snap")

    profile2 = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
        "pre_commands": ["echo 'file1.py\nfile2.py'"],
    }
    diffs = compute_diff(sid, profile2)

    pre_diffs = [d for d in diffs if d.path and d.path.startswith("pre:")]
    assert len(pre_diffs) >= 1
