"""Coverage for watch.py — _apply_repo_map_to_sections, _format_repo_map_diff, compute_diff gaps."""

import json

import pytest

from arachna.api_errors import ProfileNotFoundError, SnapshotNotFoundError
from arachna.differ import DiffSection
from arachna.gatherer import (
    _apply_repo_map_to_sections,
    _format_repo_map_added,
    _format_repo_map_diff,
    _parse_blocks_dispatch,
    _read_file_from_disk,
    _read_file_from_store,
)
from arachna.watch import compute_diff, create_snapshot


def _make_profile(directory: str, patterns=None) -> dict:
    return {
        "directories": [directory],
        "patterns": patterns or ["*.py"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }


def _setup_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )


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


def test_apply_repo_map_to_sections_modified(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
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
    result = _apply_repo_map_to_sections(sections, "rm-mod", None, profile)
    assert len(result) == 1
    assert "foo" in result[0].content


def test_apply_repo_map_to_sections_added(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
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
    result = _apply_repo_map_to_sections(sections, "rm-add", None, profile)
    assert len(result) == 1
    assert "new.py" in result[0].path or "new_func" in result[0].content


def test_apply_repo_map_to_sections_header_passthrough(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="rm-header")

    sections = [
        DiffSection(type="header", path="", content="## Changes\n"),
    ]
    result = _apply_repo_map_to_sections(sections, "rm-header", None, profile)
    assert result[0].type == "header"
    assert result[0].content == "## Changes\n"


def test_apply_repo_map_to_sections_deleted(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")

    profile = _make_profile("src")
    create_snapshot(profile=profile, name="rm-del")

    sections = [
        DiffSection(type="deleted", path="src/main.py", content="[DELETED]\n"),
    ]
    result = _apply_repo_map_to_sections(sections, "rm-del", None, profile)
    assert len(result) == 1
    assert "Removed signatures" in result[0].content or "DELETED" in result[0].content


def test_apply_repo_map_to_sections_cannot_read(tmp_path, monkeypatch):
    _setup_config(tmp_path, monkeypatch)
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
    result = _apply_repo_map_to_sections(sections, "rm-readfail", None, profile)
    assert len(result) == 1
    assert "REMOVED" in result[0].content


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


def test_read_file_from_store_not_found():
    result = _read_file_from_store("nonexistent.py", {"other.py": "sha256:abc123"})
    assert result is None


def test_read_file_from_store_invalid_hash():
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


def test_parse_blocks_dispatch_unknown_language():
    result = _parse_blocks_dispatch("function foo() {}", "unknown_lang")
    assert result == {}


def test_parse_blocks_dispatch_c_like_go():
    text = "package main\n\nfunc main() {\n    return\n}\n"
    result = _parse_blocks_dispatch(text, "go")
    assert "main" in result


def test_parse_blocks_dispatch_script_ruby():
    text = "def hello\n    puts 'hi'\nend\n"
    result = _parse_blocks_dispatch(text, "ruby")
    assert "hello" in result
