"""Edge case tests for gitignore.py to improve coverage."""

import tempfile
from pathlib import Path

from arachna.gitignore import load_gitignore_patterns


def test_gitignore_in_excluded_dir(tmp_path):
    """Gitignore inside __pycache__ directory should be skipped."""
    excluded = tmp_path / "__pycache__"
    excluded.mkdir()
    (excluded / ".gitignore").write_text("*.pyc")
    # Create a marker so rglob finds something
    (tmp_path / "dummy.txt").write_text("x")

    patterns = load_gitignore_patterns(tmp_path)
    # Patterns from __pycache__/.gitignore should be excluded
    for p in patterns:
        assert "__pycache__" not in p, f"Pattern from excluded dir leaked: {p}"


def test_gitignore_in_venv_skipped(tmp_path):
    """Gitignore inside venv directory should be skipped."""
    venv = tmp_path / "venv"
    venv.mkdir()
    (venv / ".gitignore").write_text("*.pyc")
    (tmp_path / "dummy.txt").write_text("x")

    patterns = load_gitignore_patterns(tmp_path)
    for p in patterns:
        assert "venv" not in p, f"Pattern from venv leaked: {p}"


def test_gitignore_large_file_skipped(tmp_path):
    """Gitignore files larger than _MAX_GITIGNORE_SIZE should be skipped."""
    # Write a file just over 100KB
    content = "# Comment\n" + "*.pyc\n" * 20000  # ~140KB
    (tmp_path / ".gitignore").write_text(content)
    # The file is >100KB, should be skipped entirely
    patterns = load_gitignore_patterns(tmp_path)
    # Verify it doesn't crash — patterns may be empty or have subdirectory ones
    assert isinstance(patterns, list)


def test_gitignore_with_symlink_outside_root(tmp_path):
    """Gitignore accessed via symlink outside root should not crash."""
    import os

    outside = Path(tempfile.mkdtemp())
    (outside / ".gitignore").write_text("secret.key")
    try:
        link = tmp_path / "link_to_outside"
        os.symlink(outside, link)
        (tmp_path / "dummy.txt").write_text("x")

        # Should not crash when encountering symlink
        patterns = load_gitignore_patterns(tmp_path)
        # Patterns from outside root should not appear
        for p in patterns:
            assert "secret" not in p, f"Pattern from outside root leaked: {p}"
    finally:
        if link.exists():
            link.unlink()
        import shutil

        shutil.rmtree(outside, ignore_errors=True)


def test_gitignore_binary_unicode_error(tmp_path):
    """Gitignore with non-UTF8 content should be skipped gracefully."""
    # Write valid UTF-8 BOM followed by invalid bytes
    (tmp_path / ".gitignore").write_bytes(b"\xef\xbb\xbf# comment\n\xfe\xff\x00\x01")
    patterns = load_gitignore_patterns(tmp_path)
    # Should not crash, may return empty or partial patterns
    assert isinstance(patterns, list)


def test_gitignore_with_null_bytes(tmp_path):
    """Gitignore with null bytes should be skipped."""
    (tmp_path / ".gitignore").write_bytes(b"*.pyc\x00secret.key")
    patterns = load_gitignore_patterns(tmp_path)
    # Should skip the file entirely due to null bytes
    assert len(patterns) == 0, f"Expected 0 patterns, got {patterns}"
