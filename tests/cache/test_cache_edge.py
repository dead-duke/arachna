"""Edge case tests for cache.py to improve coverage."""

import time

from arachna.cache import _file_hash, get_changed_files, save_cache


def test_file_hash_os_error(tmp_path):
    """_file_hash returns None when file raises OSError on stat."""
    f = tmp_path / "unreadable.py"
    f.write_text("hello")
    f.chmod(0o000)
    try:
        assert _file_hash(f) is None
    finally:
        f.chmod(0o644)


def test_get_changed_files_both_none_hash(tmp_path):
    """When both old and new hash are None, trust mtime change."""
    a = tmp_path / "a.py"
    a.write_text("original")
    cache = {str(a): {"mtime": 0.0, "hash": None}}
    time.sleep(0.01)
    a.write_text("modified")

    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1
    assert str(a) in [str(x) for x in changed]


def test_save_cache_fallback_direct_write(tmp_path, monkeypatch):
    """save_cache falls back to direct write when tempfile.mkstemp fails."""
    import arachna.cache as cache_module

    def failing_mkstemp(*args, **kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(cache_module.tempfile, "mkstemp", failing_mkstemp)
    save_cache(tmp_path, {"a.py": {"mtime": 1.0, "hash": "abc"}})
    assert (tmp_path / ".arachna_cache.json").exists()


def test_get_changed_files_old_hash_none(tmp_path):
    """When old hash is None but new hash exists, treat as changed."""
    a = tmp_path / "a.py"
    a.write_text("hello")
    cache = {str(a): {"mtime": 0.0, "hash": None}}
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1


def test_get_changed_files_new_hash_none(tmp_path, monkeypatch):
    """When new hash is None (large file), treat as changed."""
    a = tmp_path / "big.py"
    a.write_text("hello")

    def mock_file_hash(filepath):
        return None

    monkeypatch.setattr("arachna.cache._file_hash", mock_file_hash)
    cache = {str(a): {"mtime": 0.0, "hash": "abc"}}
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1
