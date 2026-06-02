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


def test_text_extension_never_skipped(tmp_path):
    """Files with text extensions (.py, .md, etc.) are never skipped
    regardless of include_binary flag — new behaviour in v1.5.0."""
    f = tmp_path / "main.py"
    f.write_text("print('hello')")
    # include_binary=False should NOT skip .py files
    assert not _should_skip_binary(f, False, None, 1.0)
    # include_binary=True with wrong binary_extensions should NOT skip .py files
    assert not _should_skip_binary(f, True, [".png"], 1.0)


def test_no_extension_text_file_not_skipped(tmp_path):
    """Files without extension are treated as text when include_binary=False."""
    f = tmp_path / "Dockerfile"
    f.write_text("FROM python:3.11")
    # Dockerfile has no extension but is a known filename
    # For _should_skip_binary, no-extension files with include_binary=False
    # should NOT be skipped
    f2 = tmp_path / "Makefile"
    f2.write_text("all:")
    assert not _should_skip_binary(f, False, None, 1.0)
    assert not _should_skip_binary(f2, False, None, 1.0)


def test_no_extension_binary_include_true(tmp_path):
    """Files without extension with include_binary=True and binary_extensions
    that don't include '' are skipped."""
    f = tmp_path / "unknown_binary"
    f.write_bytes(b"\x00\x01\x02")
    assert _should_skip_binary(f, True, [".bin"], 1.0)


def test_no_extension_binary_include_true_allowed(tmp_path):
    """Files without extension with include_binary=True and binary_extensions
    that include '' are NOT skipped."""
    f = tmp_path / "unknown_binary"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [""], 1.0)


def test_no_extension_size_check(tmp_path):
    """Files without extension with include_binary=True are checked for size."""
    f = tmp_path / "large_noext"
    f.write_bytes(b"x" * 2000)
    assert _should_skip_binary(f, True, None, 0.001)
