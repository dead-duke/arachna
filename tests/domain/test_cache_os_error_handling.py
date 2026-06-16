"""Tests for cache functions handling files that don't exist on disk."""

from arachna.domain.cache import get_changed_files, update_cache


def test_get_changed_files_skips_file_that_does_not_exist(tmp_path):
    """get_changed_files skips files that don't exist on disk."""
    f = tmp_path / "a.py"
    f.write_text("content")
    cache = {str(f): {"mtime_ns": 0, "size": 0, "hash": "abc"}}
    f.unlink()

    changed, new, deleted = get_changed_files([f], cache)
    assert len(changed) == 0
    assert len(new) == 0


def test_update_cache_skips_file_that_does_not_exist(tmp_path):
    """update_cache skips files that don't exist on disk."""
    f = tmp_path / "a.py"
    f.write_text("content")
    f.unlink()

    cache = update_cache([f], {})
    assert str(f) not in cache
