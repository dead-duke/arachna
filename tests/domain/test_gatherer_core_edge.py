"""Edge case tests for gatherer_core.py uncovered branches."""

from arachna.domain.gatherer_core import (
    _collect_file_sections,
    _collect_named_sections,
    _format_one_file,
    _get_profile_files,
)
from arachna.domain.tokenizer import count_tokens


def test_collect_file_sections_not_found(tmp_path):
    """_collect_file_sections skips non-existent files."""
    profile = {
        "files": ["nonexistent.py"],
        "use_gitignore": False,
    }
    sections = _collect_file_sections(profile, [], count_tokens, root=tmp_path, verbose=False)
    assert len(sections) == 0


def test_collect_file_sections_excluded(tmp_path):
    """_collect_file_sections skips excluded files."""
    f = tmp_path / "debug.log"
    f.write_text("log")

    profile = {
        "files": [str(f)],
        "use_gitignore": False,
    }
    sections = _collect_file_sections(
        profile, ["*.log"], count_tokens, root=tmp_path, verbose=False
    )
    assert len(sections) == 0


def test_get_profile_files_not_a_file(tmp_path):
    """_get_profile_files skips paths that are not files."""
    (tmp_path / "subdir").mkdir()

    profile = {"files": [str(tmp_path / "subdir")]}
    files = _get_profile_files(profile, [], root=tmp_path)
    assert len(files) == 0


def test_get_profile_files_excluded(tmp_path):
    """_get_profile_files skips excluded files."""
    f = tmp_path / "skip.me"
    f.write_text("skip")

    profile = {"files": [str(f)]}
    files = _get_profile_files(profile, ["*.me"], root=tmp_path)
    assert len(files) == 0


def test_format_one_file_returns_none_for_binary(tmp_path):
    """_format_one_file returns None when format_file_section returns empty string."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")

    result = _format_one_file(f, "markdown", False, None, 1.0, False, False, False)
    assert result is None


def test_collect_named_sections_with_query(tmp_path):
    """_collect_named_sections applies query filter."""
    (tmp_path / "main.py").write_text("def login(): pass")
    (tmp_path / "utils.py").write_text("def helper(): pass")

    profile = {
        "directories": [str(tmp_path)],
        "patterns": ["*.py"],
        "use_gitignore": False,
    }
    sections, cache = _collect_named_sections(
        profile, [], count_tokens, root=tmp_path, query="login"
    )
    names = [s[0] for s in sections]
    assert any("main.py" in n for n in names)
    assert not any("utils.py" in n for n in names)
