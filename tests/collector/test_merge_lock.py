"""Tests for _merge_lock in collector.py — platform-specific paths.

fcntl path: tested on macOS/Linux (always available).
msvcrt path: tested on Windows CI (skipped on Unix).
"""

import sys

import pytest

from arachna.collector import _find_next_part_num, _merge_lock


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
