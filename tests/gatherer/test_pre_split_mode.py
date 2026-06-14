"""Tests for unified split mode (v1.4.1)."""

from arachna.gatherer import _assemble_content
from arachna.tokenizer import count_tokens


def test_unified_split_pre_commands_and_files_together(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "utils.py").write_text("def foo(): pass")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": ["echo '=== SECTION ==='", "echo 'another section'"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "use_gitignore": False,
    }

    named_sections, parts, _indices, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(named_sections) >= 4
    assert len(parts) == 1


def test_unified_split_small_limit_many_parts(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x" * 500)
    (src / "b.py").write_text("y" * 500)

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": ["echo 'hello'"],
        "max_tokens": 10,
        "split_mode": "by_file",
        "use_gitignore": False,
    }

    named_sections, parts, _indices, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(parts) >= 3


def test_unified_split_with_compress(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": ["echo 'line1\n\n\n\nline2'"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "compress": True,
        "use_gitignore": False,
    }

    named_sections, parts, _indices, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(parts) >= 1
    for p in parts:
        assert "\n\n\n\n" not in p


def test_unified_split_without_pre_commands(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": [],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "use_gitignore": False,
    }

    named_sections, parts, _indices, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(parts) == 1


def test_unified_split_dense_packing(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(20):
        (src / f"file_{i}.py").write_text("x" * 1000)

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": ["echo 'git log output'"],
        "max_tokens": 2000,
        "split_mode": "by_file",
        "use_gitignore": False,
    }

    named_sections, parts, _indices, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(parts) >= 2, f"Expected >= 2 parts, got {len(parts)}"
    for i, part in enumerate(parts[:-1]):
        part_tokens = count_tokens(part)
        assert part_tokens >= profile["max_tokens"] * 0.5, (
            f"Part {i} has {part_tokens} tokens, expected >= {profile['max_tokens'] * 0.5}"
        )
