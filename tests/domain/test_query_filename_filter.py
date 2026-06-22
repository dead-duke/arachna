"""Tests for _filter_filenames_by_query edge cases."""

from pathlib import Path

from arachna.domain.collection.gatherer_query import _filter_filenames_by_query


def test_filter_filenames_no_match_returns_empty():
    """No matching filenames returns empty list."""
    files = [Path("src/main.py"), Path("src/utils.py")]
    result = _filter_filenames_by_query(files, "nonexistent")
    assert result == []


def test_filter_filenames_case_insensitive():
    """Filename matching is case-insensitive."""
    files = [Path("src/Auth.py")]
    result = _filter_filenames_by_query(files, "auth")
    assert len(result) == 1


def test_filter_filenames_partial_match():
    """Partial word match in filename."""
    files = [Path("src/authentication.py"), Path("src/utils.py")]
    result = _filter_filenames_by_query(files, "auth")
    assert len(result) == 1
    assert result[0].name == "authentication.py"
