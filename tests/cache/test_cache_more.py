"""Additional edge case tests for cache.py."""

import sys

import pytest

from arachna.cache import _file_hash


def test_file_hash_nonexistent():
    """_file_hash returns None for non-existent file."""
    from pathlib import Path

    assert _file_hash(Path("/nonexistent/file.txt")) is None


@pytest.mark.skipif(sys.platform == "win32", reason="chmod 0o000 does not prevent reads on Windows")
def test_file_hash_permission_denied(tmp_path):
    """_file_hash returns None for unreadable file."""
    f = tmp_path / "secret.txt"
    f.write_text("secret")
    f.chmod(0o000)
    try:
        assert _file_hash(f) is None
    finally:
        f.chmod(0o644)
