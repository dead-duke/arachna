"""Tests for verbose output branches in format_file_section."""

from arachna.domain.formatting.formatter import format_file_section


def test_verbose_os_error_on_stat(tmp_path, capsys):
    f = tmp_path / "gone.py"
    f.write_text("x")
    f.unlink()
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (error)" in captured.out


def test_verbose_skip_binary(tmp_path, capsys):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (binary)" in captured.out


def test_verbose_skip_unicode_decode_error(tmp_path, capsys):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(f, include_binary=False, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (binary)" in captured.out


def test_verbose_skip_null_bytes(tmp_path, capsys):
    f = tmp_path / "data.txt"
    f.write_bytes(b"text\x00more")
    result = format_file_section(f, include_binary=False, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (binary)" in captured.out


def test_verbose_skip_binary_large(tmp_path, capsys):
    f = tmp_path / "large.bin"
    f.write_bytes(b"\x00" * 2000)
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (binary)" in captured.out


def test_verbose_skip_binary_not_in_allowlist(tmp_path, capsys):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = format_file_section(
        f, include_binary=True, binary_extensions=[".png"], binary_max_mb=1.0, verbose=True
    )
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (binary not in allowlist)" in captured.out


def test_verbose_skip_permission_error(tmp_path, capsys):
    import sys

    import pytest

    if sys.platform == "win32":
        pytest.skip("chmod 0o000 does not work on Windows")

    f = tmp_path / "secret.py"
    f.write_text("secret")
    f.chmod(0o000)
    try:
        result = format_file_section(f, verbose=True)
        captured = capsys.readouterr()
        assert result == ""
        assert "Skipped (permission)" in captured.out
    finally:
        f.chmod(0o644)


def test_verbose_text_file_not_skipped(tmp_path, capsys):
    f = tmp_path / "main.py"
    f.write_text("print('hello')")
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result != ""
    assert "Skipped" not in captured.out
