"""Edge case tests for cache.py — error handling, fallback paths, SHA256 behaviour."""

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from arachna.domain.cache import _file_hash, get_changed_files, save_cache, update_cache

# -- _file_hash error handling --


def test_file_hash_nonexistent():
    assert _file_hash(Path("/nonexistent/file.txt")) is None


def test_file_hash_returns_none_when_file_exceeds_max_size(tmp_path):
    f = tmp_path / "big.py"
    f.write_text("x" * 100)
    with patch("arachna.domain.cache._MAX_HASH_SIZE", 50):
        assert _file_hash(f) is None


@pytest.mark.skipif(sys.platform == "win32", reason="chmod 0o000 does not prevent reads on Windows")
def test_file_hash_os_error(tmp_path):
    f = tmp_path / "unreadable.py"
    f.write_text("hello")
    f.chmod(0o000)
    try:
        assert _file_hash(f) is None
    finally:
        f.chmod(0o644)


@pytest.mark.skipif(sys.platform == "win32", reason="chmod 0o000 does not prevent reads on Windows")
def test_file_hash_permission_denied(tmp_path):
    f = tmp_path / "secret.txt"
    f.write_text("secret")
    f.chmod(0o000)
    try:
        assert _file_hash(f) is None
    finally:
        f.chmod(0o644)


# -- save_cache fallback paths --


def test_save_cache_falls_back_on_mkstemp_error(tmp_path):
    def failing_mkstemp(*args, **kwargs):
        raise OSError("No space left on device")

    with patch("tempfile.mkstemp", failing_mkstemp):
        save_cache(tmp_path, {"a.py": {"mtime_ns": 1, "size": 10, "hash": "abc"}})
    assert (tmp_path / ".arachna_cache.json").exists()


def test_save_cache_falls_back_on_replace_error(tmp_path):
    def failing_replace(src, dst):
        raise OSError("Cross-device link")

    with patch("os.replace", failing_replace):
        save_cache(tmp_path, {"a.py": {"mtime_ns": 1, "size": 10, "hash": "abc"}})
    assert (tmp_path / ".arachna_cache.json").exists()


def test_save_cache_fallback_direct_write(tmp_path, monkeypatch):
    import arachna.domain.cache as cache_module

    def failing_mkstemp(*args, **kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(cache_module.tempfile, "mkstemp", failing_mkstemp)
    save_cache(tmp_path, {"a.py": {"mtime": 1.0, "hash": "abc"}})
    assert (tmp_path / ".arachna_cache.json").exists()


# -- get_changed_files edge cases --


def test_get_changed_files_both_none_hash(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("original")
    cache = {str(a): {"mtime": 0.0, "hash": None}}
    time.sleep(0.01)
    a.write_text("modified")
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1


def test_get_changed_files_old_hash_none(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    cache = {str(a): {"mtime": 0.0, "hash": None}}
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1


def test_get_changed_files_new_hash_none(tmp_path, monkeypatch):
    a = tmp_path / "big.py"
    a.write_text("hello")

    def mock_file_hash(filepath):
        return None

    monkeypatch.setattr("arachna.domain.cache._file_hash", mock_file_hash)
    cache = {str(a): {"mtime": 0.0, "hash": "abc"}}
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1


def test_get_changed_files_skips_file_that_does_not_exist(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("content")
    cache = {str(f): {"mtime_ns": 0, "size": 0, "hash": "abc"}}
    f.unlink()
    changed, new, _ = get_changed_files([f], cache)
    assert len(changed) == 0
    assert len(new) == 0


# -- update_cache edge cases --


def test_update_cache_skips_file_that_does_not_exist(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("content")
    f.unlink()
    cache = update_cache([f], {})
    assert str(f) not in cache


# -- SHA256 fallback paths --


def test_mtime_tolerance_size_differs_hash_same(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    import hashlib

    st = a.stat()
    cache = {
        str(a): {
            "mtime_ns": st.st_mtime_ns,
            "size": 999,
            "hash": hashlib.sha256(b"hello").hexdigest(),
        }
    }
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0


def test_mtime_tolerance_size_differs_hash_differs(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    st = a.stat()
    cache = {
        str(a): {
            "mtime_ns": st.st_mtime_ns,
            "size": 999,
            "hash": "different_hash",
        }
    }
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1
