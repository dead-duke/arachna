"""Tests for file modification cache — load, save, change detection, edge cases."""

import hashlib
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from arachna.domain.cache.cache import (
    _file_hash,
    get_changed_files,
    load_cache,
    save_cache,
    update_cache,
)


def _make_entry(filepath: Path) -> dict:
    st = filepath.stat()
    return {
        "mtime_ns": st.st_mtime_ns,
        "size": st.st_size,
        "hash": hashlib.sha256(filepath.read_bytes()).hexdigest(),
    }


def test_load_cache_empty(tmp_path):
    cache = load_cache(tmp_path)
    assert cache == {}


def test_save_and_load_cache(tmp_path):
    entry = {"mtime_ns": 1734567890123456789, "size": 100, "hash": "abc"}
    save_cache(tmp_path, {"a.py": entry})
    cache = load_cache(tmp_path)
    assert cache == {"a.py": entry}


def test_save_cache_includes_version(tmp_path):
    import json

    save_cache(tmp_path, {})
    data = json.loads((tmp_path / ".arachna_cache.json").read_text())
    assert data["_version"] == 2
    assert data["files"] == {}


def test_get_changed_files_all_new(tmp_path):
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    a.write_text("hello")
    b.write_text("world")
    cache = {}
    changed, new, deleted = get_changed_files([a, b], cache)
    assert len(changed) == 0
    assert len(new) == 2
    assert len(deleted) == 0


def test_get_changed_files_none_changed(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    cache = {str(a): _make_entry(a)}
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0
    assert len(new) == 0
    assert len(deleted) == 0


def test_get_changed_files_modified(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("original")
    cache = {str(a): _make_entry(a)}
    a.write_text("modified")
    st = a.stat()
    os.utime(str(a), ns=(st.st_atime_ns, st.st_mtime_ns - 10_000_000_000))
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1
    assert len(new) == 0
    assert len(deleted) == 0


def test_get_changed_files_deleted(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    cache = {str(a): _make_entry(a)}
    a.unlink()
    changed, new, deleted = get_changed_files([], cache)
    assert len(changed) == 0
    assert len(new) == 0
    assert len(deleted) == 1


def test_get_changed_files_mixed(tmp_path):
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    c = tmp_path / "c.py"
    a.write_text("unchanged")
    b.write_text("original")
    cache = {str(a): _make_entry(a), str(b): _make_entry(b)}
    b.write_text("modified")
    st = b.stat()
    os.utime(str(b), ns=(st.st_atime_ns, st.st_mtime_ns - 10_000_000_000))
    c.write_text("new file")
    changed, new, deleted = get_changed_files([a, b, c], cache)
    assert len(changed) == 1
    assert str(b) in [str(x) for x in changed]
    assert len(new) == 1
    assert str(c) in [str(x) for x in new]
    assert len(deleted) == 0


def test_update_cache(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    cache = {}
    updated = update_cache([a], cache)
    assert str(a) in updated
    entry = updated[str(a)]
    assert "mtime_ns" in entry
    assert entry["mtime_ns"] == a.stat().st_mtime_ns
    assert "size" in entry
    assert entry["size"] == a.stat().st_size
    assert "hash" in entry
    assert isinstance(entry["hash"], str)


def test_update_cache_nonexistent_file(tmp_path):
    a = tmp_path / "ghost.py"
    cache = {}
    updated = update_cache([a], cache)
    assert str(a) not in updated


def test_get_changed_files_large_file(tmp_path):
    a = tmp_path / "big.py"
    a.write_text("hello")
    cache = {str(a): {"mtime_ns": 0, "size": a.stat().st_size, "hash": None}}
    a.write_text("modified big")
    st = a.stat()
    os.utime(str(a), ns=(st.st_atime_ns, st.st_mtime_ns - 10_000_000_000))
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1
    assert len(new) == 0


def test_get_changed_files_missing_from_disk(tmp_path):
    a = tmp_path / "ghost.py"
    cache = {}
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0
    assert len(new) == 0
    assert len(deleted) == 0


def test_save_cache_fallback(tmp_path, monkeypatch):
    import arachna.domain.cache.cache as cache_module

    def failing_mkstemp(*args, **kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(cache_module.tempfile, "mkstemp", failing_mkstemp)
    save_cache(tmp_path, {"a.py": {"mtime_ns": 1, "size": 100, "hash": "abc"}})
    assert (tmp_path / ".arachna_cache.json").exists()


def test_mtime_ns_unchanged_skipped(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    cache = {str(a): _make_entry(a)}
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0
    assert len(new) == 0


def test_mtime_ns_false_positive(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("unchanged content")
    cache = {str(a): _make_entry(a)}
    old_mtime_ns = cache[str(a)]["mtime_ns"]
    a.write_text("unchanged content")
    st = a.stat()
    os.utime(str(a), ns=(st.st_atime_ns, st.st_mtime_ns + 10_000_000_000))
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0
    assert cache[str(a)]["mtime_ns"] > old_mtime_ns


def test_size_changed_real_modification(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("short")
    cache = {str(a): _make_entry(a)}
    a.write_text("much longer content now")
    st = a.stat()
    os.utime(str(a), ns=(st.st_atime_ns, st.st_mtime_ns - 10_000_000_000))
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1


def test_mtime_ns_within_tolerance(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    st = a.stat()
    cache = {
        str(a): {
            "mtime_ns": st.st_mtime_ns - 100,
            "size": st.st_size,
            "hash": _make_entry(a)["hash"],
        }
    }
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0


def test_mtime_ns_exceeds_tolerance(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    st = a.stat()
    cache = {
        str(a): {
            "mtime_ns": st.st_mtime_ns - 2_000_000,
            "size": st.st_size,
            "hash": _make_entry(a)["hash"],
        }
    }
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0


def test_cache_migration_old_format(tmp_path):
    import json

    a = tmp_path / "a.py"
    a.write_text("hello")
    old_cache = {str(a): {"mtime": 1.0, "hash": "abc"}}
    (tmp_path / ".arachna_cache.json").write_text(json.dumps(old_cache))
    cache = load_cache(tmp_path)
    assert cache == {}, f"Expected empty cache after migration, got {cache}"


def test_mtime_ns_none_hash(tmp_path):
    a = tmp_path / "big.py"
    a.write_text("hello")
    cache = {str(a): {"mtime_ns": 0, "size": a.stat().st_size, "hash": None}}
    a.write_text("modified")
    st = a.stat()
    os.utime(str(a), ns=(st.st_atime_ns, st.st_mtime_ns - 10_000_000_000))
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1


# Edge cases


def test_file_hash_nonexistent():
    assert _file_hash(Path("/nonexistent/file.txt")) is None


def test_file_hash_returns_none_when_file_exceeds_max_size(tmp_path):
    f = tmp_path / "big.py"
    f.write_text("x" * 100)
    with patch("arachna.domain.cache.cache._MAX_HASH_SIZE", 50):
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
    import arachna.domain.cache.cache as cache_module

    def failing_mkstemp(*args, **kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(cache_module.tempfile, "mkstemp", failing_mkstemp)
    save_cache(tmp_path, {"a.py": {"mtime": 1.0, "hash": "abc"}})
    assert (tmp_path / ".arachna_cache.json").exists()


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


def test_update_cache_skips_file_that_does_not_exist(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("content")
    f.unlink()
    cache = update_cache([f], {})
    assert str(f) not in cache


def test_mtime_tolerance_size_differs_hash_same(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
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
