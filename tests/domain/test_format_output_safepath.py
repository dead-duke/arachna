"""Tests for format_file_section with SafePath validation."""

from pathlib import Path

from arachna.domain.formatting.formatter import format_file_section


def test_format_file_section_path_traversal_rejected(tmp_path):
    """Path outside root raises no error — returns empty string."""
    outside = Path("/etc/passwd")
    result = format_file_section(outside, root=tmp_path)
    assert result == ""


def test_format_file_section_path_traversal_verbose(tmp_path, capsys):
    """Path outside root with verbose — prints skipped message."""
    outside = Path("/etc/passwd")
    result = format_file_section(outside, root=tmp_path, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped" in captured.out
