"""Tests for _merge_lock in collector.py — platform-specific paths.

fcntl path: tested on macOS/Linux (always available).
msvcrt path: tested on Windows CI (skipped on Unix).
Mock path: msvcrt + sys.platform on Unix to cover the branch.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from arachna.domain.collection.collector import (
    _find_next_part_num,
    _get_lock_functions,
    _merge_lock,
)


def test_merge_lock_context_manager(tmp_path):
    """_merge_lock acquires and releases without error."""
    out = tmp_path / "out"
    out.mkdir()
    with _merge_lock(out):
        (out / "test.txt").write_text("locked")
    assert not (out / ".arachna_merge.lock").exists()


def test_find_next_part_num_under_lock(tmp_path):
    """_find_next_part_num acquires lock internally."""
    out = tmp_path / "out"
    out.mkdir()
    assert _find_next_part_num(out, "chat-c") == 1


@pytest.mark.skipif(sys.platform != "win32", reason="msvcrt is Windows-only")
def test_merge_lock_windows_msvcrt(tmp_path):
    """Windows path: msvcrt.locking is used when fcntl not available."""
    out = tmp_path / "out"
    out.mkdir()
    with _merge_lock(out):
        pass


def test_find_next_part_num_existing_with_lock(tmp_path):
    """_find_next_part_num with existing files under lock."""
    out = tmp_path / "out"
    out.mkdir()
    (out / "chat-c_1.md").write_text("x")
    (out / "chat-c_2.md").write_text("x")
    assert _find_next_part_num(out, "chat-c") == 3


def test_merge_lock_msvcrt_on_unix_mocked(tmp_path):
    """Mock msvcrt import on Unix to cover the Windows code path (LOW-19)."""
    mock_msvcrt = MagicMock()
    mock_msvcrt.LK_LOCK = 1
    mock_msvcrt.LK_UNLCK = 2

    with patch.dict(sys.modules, {"fcntl": None, "msvcrt": mock_msvcrt}):
        # Clear lru_cache so the mocked modules take effect
        _get_lock_functions.cache_clear()
        try:
            out = tmp_path / "out"
            out.mkdir()
            with _merge_lock(out):
                (out / "test.txt").write_text("locked")
            assert not (out / ".arachna_merge.lock").exists()
        finally:
            _get_lock_functions.cache_clear()
