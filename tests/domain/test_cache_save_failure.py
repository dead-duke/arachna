"""Tests for save_cache error handling paths."""

from unittest.mock import patch

from arachna.domain.cache import save_cache


def test_save_cache_falls_back_on_mkstemp_error(tmp_path):
    """save_cache uses direct write when mkstemp raises OSError."""

    def failing_mkstemp(*args, **kwargs):
        raise OSError("No space left on device")

    with patch("tempfile.mkstemp", failing_mkstemp):
        save_cache(tmp_path, {"a.py": {"mtime_ns": 1, "size": 10, "hash": "abc"}})

    assert (tmp_path / ".arachna_cache.json").exists()


def test_save_cache_falls_back_on_replace_error(tmp_path):
    """save_cache uses direct write fallback when os.replace raises OSError."""

    def failing_replace(src, dst):
        raise OSError("Cross-device link")

    with patch("os.replace", failing_replace):
        save_cache(tmp_path, {"a.py": {"mtime_ns": 1, "size": 10, "hash": "abc"}})

    assert (tmp_path / ".arachna_cache.json").exists()
