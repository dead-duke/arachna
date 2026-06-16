"""Tests for remaining uncovered branches in formatter.py."""

from unittest.mock import patch

from arachna.domain.formatter import (
    _lang_from_shebang,
    _parse_python,
    _should_skip_binary,
    format_file_section,
)


def test_shebang_env_without_interpreter():
    """Shebang with /usr/bin/env but no interpreter returns empty string."""
    assert _lang_from_shebang("#!/usr/bin/env") == ""


def test_should_skip_binary_include_false_os_error(tmp_path):
    """OSError on stat with include_binary=False returns True (skip)."""
    f = tmp_path / "gone.bin"
    f.write_bytes(b"\x00")
    f.unlink()
    assert _should_skip_binary(f, False, None, 1.0)


def test_format_file_section_unicode_decode_fallback(tmp_path, capsys):
    """UnicodeDecodeError with include_binary=False but binary not allowed."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(f, include_binary=True, binary_extensions=[".png"], verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "not in allowlist" in captured.out


def test_format_file_section_permission_error_silent(tmp_path):
    """PermissionError without verbose returns empty string silently."""
    f = tmp_path / "secret.py"
    f.write_text("secret")

    def failing_read_text(*args, **kwargs):
        raise PermissionError("Denied")

    with patch("pathlib.Path.read_text", failing_read_text):
        result = format_file_section(f, verbose=False)
    assert result == ""


def test_parse_python_syntax_error_multiline_import():
    """SyntaxError fallback correctly parses multiline imports."""
    text = "import (\n    os,\n    sys\n)\ndef foo(:\n    pass\n"
    deps, exports = _parse_python(text)
    assert "os" in deps
    assert "sys" in deps


def test_parse_python_syntax_error_with_from_import():
    """SyntaxError fallback handles 'from X import Y' style."""
    text = "from pathlib import Path\ndef foo(:\n    pass\n"
    deps, exports = _parse_python(text)
    assert "pathlib" in deps


def test_parse_python_syntax_error_no_imports():
    """SyntaxError fallback with no imports returns empty deps."""
    text = "def foo(:\n    pass\n"
    deps, exports = _parse_python(text)
    assert deps == []
    assert exports == []
