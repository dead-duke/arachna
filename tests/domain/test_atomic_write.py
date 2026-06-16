"""Tests for atomic_write.py fallback paths."""

import contextlib
from unittest.mock import patch

from arachna.domain.atomic_write import atomic_write_bytes, atomic_write_text


def test_atomic_write_text_mkstemp_fallback(tmp_path):
    """When mkstemp fails with OSError, falls back to Path.write_text."""
    f = tmp_path / "sub" / "test.txt"

    def failing_mkstemp(*args, **kwargs):
        raise OSError("No space left on device")

    with patch("arachna.domain.atomic_write.tempfile.mkstemp", failing_mkstemp):
        atomic_write_text(f, "fallback content")

    assert f.exists()
    assert f.read_text() == "fallback content"


def test_atomic_write_text_os_replace_fails_falls_back(tmp_path):
    """When os.replace fails with OSError, outer except catches it and falls back to write_text."""
    f = tmp_path / "test.txt"

    def failing_replace(src, dst):
        raise OSError("Cross-device link")

    with patch("arachna.domain.atomic_write.os.replace", failing_replace):
        atomic_write_text(f, "fallback content")

    assert f.exists()
    assert f.read_text() == "fallback content"


def test_atomic_write_text_inner_exception_cleanup(tmp_path):
    """When inner block fails with non-OSError, tmp file is cleaned up and error propagates."""
    f = tmp_path / "test.txt"

    def failing_fdopen(fd, mode, encoding=None):
        raise RuntimeError("Unexpected error")

    with (
        patch("arachna.domain.atomic_write.os.fdopen", failing_fdopen),
        patch("arachna.domain.atomic_write.os.unlink") as mock_unlink,
    ):
        with contextlib.suppress(RuntimeError):
            atomic_write_text(f, "content")
        mock_unlink.assert_called_once()


def test_atomic_write_bytes_mkstemp_fallback(tmp_path):
    """When mkstemp fails with OSError, falls back to Path.write_bytes."""
    f = tmp_path / "sub" / "test.bin"

    def failing_mkstemp(*args, **kwargs):
        raise OSError("No space left on device")

    with patch("arachna.domain.atomic_write.tempfile.mkstemp", failing_mkstemp):
        atomic_write_bytes(f, b"fallback bytes")

    assert f.exists()
    assert f.read_bytes() == b"fallback bytes"


def test_atomic_write_bytes_os_replace_fails_falls_back(tmp_path):
    """When os.replace fails with OSError, outer except catches it and falls back to write_bytes."""
    f = tmp_path / "test.bin"

    def failing_replace(src, dst):
        raise OSError("Cross-device link")

    with patch("arachna.domain.atomic_write.os.replace", failing_replace):
        atomic_write_bytes(f, b"fallback bytes")

    assert f.exists()
    assert f.read_bytes() == b"fallback bytes"


def test_atomic_write_bytes_inner_exception_cleanup(tmp_path):
    """When inner block fails with non-OSError, tmp file is cleaned up and error propagates."""
    f = tmp_path / "test.bin"

    def failing_fdopen(fd, mode):
        raise RuntimeError("Unexpected error")

    with (
        patch("arachna.domain.atomic_write.os.fdopen", failing_fdopen),
        patch("arachna.domain.atomic_write.os.unlink") as mock_unlink,
    ):
        with contextlib.suppress(RuntimeError):
            atomic_write_bytes(f, b"content")
        mock_unlink.assert_called_once()
