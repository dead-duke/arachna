"""Edge case tests for gitignore.py to improve coverage."""

import tempfile
from pathlib import Path

from arachna.domain.gitignore import load_gitignore_patterns


def test_gitignore_in_excluded_dir(tmp_path):
    excluded = tmp_path / "__pycache__"
    excluded.mkdir()
    (excluded / ".gitignore").write_text("*.pyc")
    (tmp_path / "dummy.txt").write_text("x")

    patterns = load_gitignore_patterns(tmp_path)
    for p in patterns:
        assert "__pycache__" not in p, f"Pattern from excluded dir leaked: {p}"


def test_gitignore_in_venv_skipped(tmp_path):
    venv = tmp_path / "venv"
    venv.mkdir()
    (venv / ".gitignore").write_text("*.pyc")
    (tmp_path / "dummy.txt").write_text("x")

    patterns = load_gitignore_patterns(tmp_path)
    for p in patterns:
        assert "venv" not in p, f"Pattern from venv leaked: {p}"


def test_gitignore_large_file_skipped(tmp_path):
    content = "# Comment\n" + "*.pyc\n" * 20000
    (tmp_path / ".gitignore").write_text(content)
    patterns = load_gitignore_patterns(tmp_path)
    assert isinstance(patterns, list)


def test_gitignore_with_symlink_outside_root(tmp_path):
    import os
    import shutil

    outside = Path(tempfile.mkdtemp())
    (outside / ".gitignore").write_text("secret.key")
    try:
        link = tmp_path / "link_to_outside"
        os.symlink(outside, link)
        (tmp_path / "dummy.txt").write_text("x")

        patterns = load_gitignore_patterns(tmp_path)
        for p in patterns:
            assert "secret" not in p, f"Pattern from outside root leaked: {p}"
    finally:
        if link.exists():
            link.unlink()
        shutil.rmtree(outside, ignore_errors=True)


def test_gitignore_binary_unicode_error(tmp_path):
    (tmp_path / ".gitignore").write_bytes(b"\xef\xbb\xbf# comment\n\xfe\xff\x00\x01")
    patterns = load_gitignore_patterns(tmp_path)
    assert isinstance(patterns, list)


def test_gitignore_with_null_bytes(tmp_path):
    (tmp_path / ".gitignore").write_bytes(b"*.pyc\x00secret.key")
    patterns = load_gitignore_patterns(tmp_path)
    assert len(patterns) == 0, f"Expected 0 patterns, got {patterns}"
