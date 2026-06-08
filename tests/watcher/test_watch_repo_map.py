"""Coverage for watch.py — _apply_repo_map_diff, _format_repo_map_diff, compute_diff gaps."""

import json

import pytest

from arachna.api_errors import ProfileNotFoundError, SnapshotNotFoundError
from arachna.differ import DiffSection
from arachna.watch import (
    _apply_repo_map_diff,
    _format_repo_map_added,
    _format_repo_map_diff,
    _parse_blocks,
    _read_file_from_disk,
    _read_file_from_store,
    compute_diff,
    create_snapshot,
)


def _make_profile(directory: str, patterns=None) -> dict:
    return {
        "directories": [directory],
        "patterns": patterns or ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


# ── _format_repo_map_diff ─────────────────────────────────────────


def test_format_repo_map_diff_sig_changed():
    old_blocks = {"foo": ("def foo(x):", "    return x")}
    new_blocks = {"foo": ("def foo(x, y=0):", "    return x")}
    result = _format_repo_map_diff("src/main.py", "python", old_blocks, new_blocks)
    assert "~" in result
    assert "->" in result


def test_format_repo_map_diff_body_changed():
    old_blocks = {"foo": ("def foo():", "    return 1")}
    new_blocks = {"foo": ("def foo():", "    return 2")}
    result = _format_repo_map_diff("src/main.py", "python", old_blocks, new_blocks)
    assert "body changed" in result


def test_format_repo_map_diff_added_block():
    old_blocks = {}
    new_blocks = {"bar": ("def bar():", "    pass")}
    result = _format_repo_map_diff("src/main.py", "python", old_blocks, new_blocks)
    assert "+" in result
    assert "bar" in result


def test_format_repo_map_diff_deleted_block():
    old_blocks = {"foo": ("def foo():", "    return 1")}
    new_blocks = {}
    result = _format_repo_map_diff("src/main.py", "python", old_blocks, new_blocks)
    assert "-" in result
    assert "foo" in result


def test_format_repo_map_diff_empty():
    result = _format_repo_map_diff("src/main.py", "python", {}, {})
    assert result == ""


# ── _format_repo_map_added ────────────────────────────────────────


def test_format_repo_map_added_with_blocks():
    blocks = {
        "foo": ("def foo():", "    pass"),
        "bar": ("def bar():", "    pass"),
    }
    result = _format_repo_map_added("src/new.py", "python", blocks)
    assert "+ def foo():" in result
    assert "+ def bar():" in result


def test_format_repo_map_added_empty():
    result = _format_repo_map_added("src/new.py", "python", {})
    assert result == ""


# ── _apply_repo_map_diff ──────────────────────────────────────────


def test_apply_repo_map_diff_modified(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="rm-mod")
    (src / "main.py").write_text("def foo():\n    return 2\n")

    sections = [
        DiffSection(
            type="modified",
            path="src/main.py",
            content="### src/main.py\n\nREMOVED lines 1:\n    old\n\nADDED lines 1:\n    new\n",
        ),
    ]
    result = _apply_repo_map_diff(sections, "rm-mod", None, profile)
    assert len(result) == 1
    assert "foo" in result[0].content


def test_apply_repo_map_diff_added(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="rm-add")

    sections = [
        DiffSection(
            type="added",
            path="src/new.py",
            content="ADDED (new file):\n\n```\ndef new_func():\n    pass\n```\n",
        ),
    ]
    result = _apply_repo_map_diff(sections, "rm-add", None, profile)
    assert len(result) == 1
    assert "new.py" in result[0].path or "new_func" in result[0].content


def test_apply_repo_map_diff_header_passthrough(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="rm-header")

    sections = [
        DiffSection(type="header", path="", content="## Changes\n"),
    ]
    result = _apply_repo_map_diff(sections, "rm-header", None, profile)
    assert result[0].type == "header"
    assert result[0].content == "## Changes\n"


def test_apply_repo_map_diff_deleted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="rm-del")

    sections = [
        DiffSection(type="deleted", path="src/main.py", content="[DELETED]\n"),
    ]
    result = _apply_repo_map_diff(sections, "rm-del", None, profile)
    assert len(result) == 1
    assert "Removed signatures" in result[0].content or "DELETED" in result[0].content


def test_apply_repo_map_diff_cannot_read_content(tmp_path, monkeypatch):
    """Repo-map falls back to text diff when file content cannot be read from store."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="rm-readfail")

    sections = [
        DiffSection(
            type="modified",
            path="nonexistent.py",
            content="### nonexistent.py\n\nREMOVED lines 1:\n    old\n",
        ),
    ]
    result = _apply_repo_map_diff(sections, "rm-readfail", None, profile)
    assert len(result) == 1
    # Content unchanged — fallback, keeps text diff
    assert "REMOVED" in result[0].content


# ── compute_diff branches ────────────────────────────────────────


def test_compute_diff_profile_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}})
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x")

    with pytest.raises(ProfileNotFoundError):
        compute_diff(profile="nonexistent", snapshot_id="no-such")


def test_compute_diff_snapshot_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x")

    profile = _make_profile("src")
    with pytest.raises(SnapshotNotFoundError):
        compute_diff(profile=profile)


# ── _read_file_from_store / _read_file_from_disk ──────────────────


def test_read_file_from_store_not_found():
    result = _read_file_from_store("nonexistent.py", {"other.py": "sha256:abc123"})
    assert result is None


def test_read_file_from_store_invalid_hash():
    """_read_file_from_store returns None when hash is invalid."""
    result = _read_file_from_store("test.py", {"test.py": "sha256:invalidhash"})
    assert result is None


def test_read_file_from_disk_not_found(tmp_path):
    result = _read_file_from_disk(str(tmp_path / "ghost.py"))
    assert result is None


def test_read_file_from_disk_not_a_file(tmp_path):
    result = _read_file_from_disk(str(tmp_path))
    assert result is None


def test_read_file_from_disk_unreadable(tmp_path):
    import sys

    if sys.platform == "win32":
        pytest.skip("chmod 0o000 does not work on Windows")

    f = tmp_path / "secret.py"
    f.write_text("secret")
    f.chmod(0o000)
    try:
        result = _read_file_from_disk(str(f))
        assert result is None
    finally:
        f.chmod(0o644)


# ── _parse_blocks coverage ────────────────────────────────────────


def test_parse_blocks_unknown_language():
    """_parse_blocks returns empty dict for unknown languages."""
    result = _parse_blocks("function foo() {}", "unknown_lang")
    assert result == {}


def test_parse_blocks_c_like_go():
    """_parse_blocks dispatches to C-like parser for Go."""
    text = "package main\n\nfunc main() {\n    return\n}\n"
    result = _parse_blocks(text, "go")
    assert "main" in result


def test_parse_blocks_script_ruby():
    """_parse_blocks dispatches to script parser for Ruby."""
    text = "def hello\n    puts 'hi'\nend\n"
    result = _parse_blocks(text, "ruby")
    assert "hello" in result
