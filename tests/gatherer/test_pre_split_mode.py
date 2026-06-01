"""Tests for unified split mode (v1.4.1).

pre_split_mode/pre_split_marker removed — all sections are now
collected into a single list and packed densely via split_sections().
"""

from arachna.gatherer import _assemble_content
from arachna.tokenizer import count_tokens


def test_unified_split_pre_commands_and_files_together(tmp_path, monkeypatch):
    """pre_commands and files are packed together in one part."""
    monkeypatch.chdir(tmp_path)
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
    # All content in one part (max_tokens large enough)
    assert len(parts) == 1


def test_unified_split_small_limit_many_parts(tmp_path, monkeypatch):
    """Small max_tokens produces multiple parts, all densely packed."""
    monkeypatch.chdir(tmp_path)
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

    named_sections, parts, new_cache = _assemble_content(
        profile,
        exclude=[],
        tokenizer=count_tokens,
        incremental=False,
        cache=None,
        verbose=False,
    )

    # Each file section is ~130 chars → ~32 tokens → too big for max_tokens=10
    # → each goes as-is in its own part → 1 pre + 2 files = 3 parts
    assert len(parts) >= 3


def test_unified_split_with_compress(tmp_path, monkeypatch):
    """Compress works with unified split."""
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
    # Blank lines collapsed: 3+ → 2
    for p in parts:
        assert "\n\n\n\n" not in p


def test_unified_split_without_pre_commands(tmp_path, monkeypatch):
    """Works without pre_commands — files still split normally."""
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

    assert len(parts) == 1


def test_unified_split_dense_packing(tmp_path, monkeypatch):
    """All parts except the last are densely packed (>= 50% of max_tokens)."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    # Create many small files — each ~250 tokens
    for i in range(20):
        (src / f"file_{i}.py").write_text("x" * 1000)

    profile = {
        "directories": ["src"],
        "patterns": ["*.py"],
        "pre_commands": ["echo 'git log output'"],
        "max_tokens": 2000,  # Each file ≈ 250 tokens → ~8 files per part
        "split_mode": "by_file",
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

    assert len(parts) >= 2, f"Expected >= 2 parts, got {len(parts)}"
    # All parts except last should be densely packed (>= 50% of max_tokens)
    for i, part in enumerate(parts[:-1]):
        part_tokens = count_tokens(part)
        assert part_tokens >= profile["max_tokens"] * 0.5, (
            f"Part {i} has {part_tokens} tokens, expected >= {profile['max_tokens'] * 0.5}"
        )
