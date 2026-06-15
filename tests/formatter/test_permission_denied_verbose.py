"""Tests for permission denied verbose output in format_file_section."""

import sys

import pytest

from arachna.domain.formatter import format_file_section


@pytest.mark.skipif(sys.platform == "win32", reason="chmod 0o000 does not work on Windows")
def test_verbose_permission_denied(tmp_path, capsys):
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
