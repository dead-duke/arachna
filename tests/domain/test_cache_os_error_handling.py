"""Tests for cache functions handling OSError on file stat."""

from arachna.domain.cache import get_changed_files, update_cache


def test_get_changed_files_skips_file_on_stat_error(tmp_path):
    """get_changed_files skips files that raise OSError on stat()."""
    f = tmp_path / "a.py"
    f.write_text("content")

    def mock_stat_error(self):
        raise OSError("Cannot stat")

    with __import__("unittest").mock.patch("pathlib.Path.stat", mock_stat_error):
        changed, new, deleted = get_changed_files([f], {})
    assert len(changed) == 0
    assert len(new) == 0


def test_update_cache_skips_file_on_stat_error(tmp_path):
    """update_cache skips files that raise OSError on stat()."""
    f = tmp_path / "a.py"
    f.write_text("content")

    def mock_stat_error(self):
        raise OSError("Cannot stat")

    with __import__("unittest").mock.patch("pathlib.Path.stat", mock_stat_error):
        cache = update_cache([f], {})
    assert str(f) not in cache
