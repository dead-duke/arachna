"""Tests for gitignore parser."""

import tempfile
from pathlib import Path

from arachna.gitignore import load_gitignore_patterns


def test_load_gitignore_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        patterns = load_gitignore_patterns(root)
        assert patterns == []


def test_load_gitignore_simple():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / ".gitignore").write_text("*.pyc\n__pycache__/\n")
        patterns = load_gitignore_patterns(root)
        assert len(patterns) > 0


def test_load_gitignore_comments_and_blanks():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / ".gitignore").write_text("# comment\n\n*.pyc\n\n# another comment\n")
        patterns = load_gitignore_patterns(root)
        assert len(patterns) == 1


def test_load_gitignore_subdirectories():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        sub = root / "sub"
        sub.mkdir()
        (root / ".gitignore").write_text("*.pyc")
        (sub / ".gitignore").write_text("*.log")
        patterns = load_gitignore_patterns(root)
        assert len(patterns) >= 2


def test_load_gitignore_nonexistent():
    patterns = load_gitignore_patterns(Path("/nonexistent/path"))
    assert patterns == []


def test_load_gitignore_binary_file_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / ".gitignore").write_bytes(b"\x00\x01\x02")
        patterns = load_gitignore_patterns(root)
        assert patterns == []
