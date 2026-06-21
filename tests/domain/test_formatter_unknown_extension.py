"""BUG-002 regression: unknown extensions checked for null bytes before skipping."""

from arachna.domain.formatting.formatter import _should_skip_binary, format_file_section


def test_unknown_extension_text_file_not_skipped(tmp_path):
    """Text file with unknown extension should not be skipped when include_binary=False."""
    f = tmp_path / "manual.1"
    f.write_text(".TH MANUAL 1\n.SH NAME\nmanual - test")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_unknown_extension_binary_file_skipped(tmp_path):
    """Binary file with unknown extension should still be skipped."""
    f = tmp_path / "data.xyz"
    f.write_bytes(b"\x00\x01\x02")
    assert _should_skip_binary(f, False, None, 1.0)


def test_format_file_section_man_page(tmp_path):
    """Man page with .1 extension is formatted as nroff."""
    f = tmp_path / "test.1"
    f.write_text(".TH TEST 1\n.SH NAME\ntest - example")
    result = format_file_section(f)
    assert result != ""
    assert "```nroff" in result


def test_format_file_section_unknown_text_extension(tmp_path):
    """Text file with completely unknown extension should be read."""
    f = tmp_path / "data.xyz"
    f.write_text("plain text content")
    result = format_file_section(f)
    assert result != ""
    assert "plain text content" in result
