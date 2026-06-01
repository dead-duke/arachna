"""Tests for verbose output branches in format_file_section."""

from arachna.formatter import format_file_section


def test_verbose_os_error_on_stat(tmp_path, capsys):
    """Verbose mode prints skip reason when stat fails."""
    f = tmp_path / "gone.py"
    f.write_text("x")
    f.unlink()
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (error)" in captured.out


def test_verbose_skip_binary(tmp_path, capsys):
    """Verbose mode prints skip reason for binary files."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (binary)" in captured.out


def test_verbose_skip_unicode_decode_error(tmp_path, capsys):
    """Verbose mode prints skip reason for non-UTF8 files."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(f, include_binary=False, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (binary)" in captured.out


def test_verbose_skip_null_bytes(tmp_path, capsys):
    """Verbose mode prints skip reason for files with null bytes."""
    f = tmp_path / "data.txt"
    f.write_bytes(b"text\x00more")
    result = format_file_section(f, include_binary=False, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (binary)" in captured.out


def test_verbose_skip_binary_large(tmp_path, capsys):
    """Verbose mode prints skip reason for large binary files.

    The code first checks extension + size before read_text. A .bin file
    with unknown extension and size > 1 MB would be 'binary too large',
    but size < 1 MB falls into the generic 'binary' skip.
    This test verifies the generic binary skip message for files under 1 MB.
    """
    f = tmp_path / "large.bin"
    # 2000 bytes — under 1 MB, will hit generic binary skip
    f.write_bytes(b"\x00" * 2000)
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    # The file is .bin (unknown ext) → binary, size 2000 < 1 MB → "Skipped (binary)"
    assert "Skipped (binary)" in captured.out
