"""Tests for format_output UnicodeDecodeError with binary allowed."""

from arachna.domain.formatting.formatter import format_file_section


def test_unicode_decode_error_binary_allowed_but_wrong_extension(tmp_path, capsys):
    """UnicodeDecodeError with binary_extensions that don't match."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(
        f, include_binary=True, binary_extensions=[".png"], binary_max_mb=1.0, verbose=True
    )
    captured = capsys.readouterr()
    assert result == ""
    assert "not in allowlist" in captured.out


def test_unicode_decode_error_binary_allowed_correct_extension(tmp_path):
    """UnicodeDecodeError with matching binary_extensions returns base64."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(
        f, include_binary=True, binary_extensions=[".bin"], binary_max_mb=1.0
    )
    assert "```base64" in result
