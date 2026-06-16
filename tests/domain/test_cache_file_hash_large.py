"""Tests for _file_hash behaviour with large files."""

from unittest.mock import patch

from arachna.domain.cache import _file_hash


def test_file_hash_returns_none_when_file_exceeds_max_size(tmp_path):
    """_file_hash returns None for files larger than _MAX_HASH_SIZE."""
    f = tmp_path / "big.py"
    f.write_text("x" * 100)

    with patch("arachna.domain.cache._MAX_HASH_SIZE", 50):
        result = _file_hash(f)
    assert result is None
