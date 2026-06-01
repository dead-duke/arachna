"""Tests for _should_skip_binary function."""

from pathlib import Path

from arachna.formatter import _should_skip_binary


def test_nonexistent_file_skipped():
    """Non-existent file returns True (should skip)."""
    assert _should_skip_binary(Path("/nonexistent/file.bin"), True, None, 1.0)


def test_file_too_large_skipped(tmp_path):
    """File over binary_max_mb returns True (should skip)."""
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * 2000)
    assert _should_skip_binary(f, True, None, 0.001)


def test_wrong_extension_skipped(tmp_path):
    """File not in binary_extensions returns True (should skip)."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".png"], 1.0)


def test_include_binary_false_skipped(tmp_path):
    """include_binary=False returns True (should skip)."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, False, None, 1.0)


def test_allowed_binary_not_skipped(tmp_path):
    """Binary file matching all criteria returns False (should not skip)."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [".bin"], 1.0)


def test_os_error_on_stat(tmp_path):
    """File that raises OSError on stat returns True (should skip)."""
    f = tmp_path / "gone.bin"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, True, None, 1.0)


def test_no_extension_allowed_with_empty_list(tmp_path):
    """No extension file with binary_extensions=[''] passes."""
    f = tmp_path / "data"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [""], 1.0)


def test_no_extension_skipped_with_other_list(tmp_path):
    """No extension file skipped when binary_extensions doesn't include ''."""
    f = tmp_path / "data"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".png"], 1.0)


def test_binary_extensions_none_allows_all(tmp_path):
    """binary_extensions=None allows all extensions."""
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, None, 1.0)
