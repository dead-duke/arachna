import tempfile
from pathlib import Path

from arachna.domain.execution.gitignore import load_gitignore_patterns


def test_empty():
    with tempfile.TemporaryDirectory() as d:
        assert load_gitignore_patterns(Path(d)) == []


def test_simple():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".gitignore").write_text("*.pyc\n__pycache__/\n")
        assert len(load_gitignore_patterns(Path(d))) > 0


def test_comments():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".gitignore").write_text("# c\n\n*.pyc\n")
        assert len(load_gitignore_patterns(Path(d))) == 1


def test_subdirectories():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "sub").mkdir()
        (Path(d) / ".gitignore").write_text("*.pyc")
        (Path(d) / "sub" / ".gitignore").write_text("*.log")
        assert len(load_gitignore_patterns(Path(d))) >= 2


def test_nonexistent():
    assert load_gitignore_patterns(Path("/nonexistent")) == []


def test_binary_skipped():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".gitignore").write_bytes(b"\x00\x01\x02")
        assert load_gitignore_patterns(Path(d)) == []


def test_skips_directory_named_gitignore():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".gitignore").mkdir()
        assert load_gitignore_patterns(Path(d)) == []


def test_leading_slash():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".gitignore").write_text("/dist\n/node_modules\n")
        patterns = load_gitignore_patterns(Path(d))
        assert len(patterns) == 2
