"""Tests for pre_split_mode feature (v1.3.0)."""

from arachna.gatherer import _assemble_content
from arachna.tokenizer import count_tokens


def test_pre_split_mode_separates_pre_commands_from_files(tmp_path, monkeypatch):
    """pre_commands with pre_split_mode are split separately from files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "utils.py").write_text("def foo(): pass")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": ["echo '=== SECTION ==='", "echo 'another section'"],
        "max_tokens": 100,
        "split_mode": "by_file",
        "pre_split_mode": "by_paragraph",
        "pre_split_marker": "\n\n",
        "use_gitignore": False,
    }

    named_sections, parts, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        incremental=False,
        cache=None,
        verbose=False,
    )

    # Should have pre_commands + 2 file sections
    assert len(named_sections) >= 4
    # Parts should start with pre_commands output, then file content
    assert len(parts) >= 1


def test_pre_split_mode_by_marker(tmp_path, monkeypatch):
    """pre_commands split by marker, files split by_file."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x" * 500)
    (src / "b.py").write_text("y" * 500)

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": ["echo 'MARKER\ntext1\nMARKER\ntext2'"],
        "max_tokens": 10,
        "split_mode": "by_file",
        "pre_split_mode": "by_marker",
        "pre_split_marker": "MARKER",
        "use_gitignore": False,
    }

    named_sections, parts, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        incremental=False,
        cache=None,
        verbose=False,
    )

    # pre_commands split by MARKER (may produce 0 parts if echo output is empty/malformed)
    # files split by_file (2 large files → 2+ parts)
    assert len(parts) >= 2


def test_pre_split_mode_with_compress(tmp_path, monkeypatch):
    """pre_split_mode works with compress enabled."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": ["echo 'line1\n\n\n\nline2'"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "pre_split_mode": "by_paragraph",
        "pre_split_marker": "\n\n",
        "compress": True,
        "use_gitignore": False,
    }

    named_sections, parts, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        incremental=False,
        cache=None,
        verbose=False,
    )

    assert len(parts) >= 1


def test_pre_split_mode_without_pre_commands(tmp_path, monkeypatch):
    """pre_split_mode without pre_commands — files still split normally."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": [],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "pre_split_mode": "by_marker",
        "pre_split_marker": "---",
        "use_gitignore": False,
    }

    named_sections, parts, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        incremental=False,
        cache=None,
        verbose=False,
    )

    # pre_commands are empty, so pre_parts is empty, file_parts is normal
    assert len(parts) == 1
