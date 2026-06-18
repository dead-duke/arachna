"""Edge case tests for formatter.py uncovered branches."""

import json
from pathlib import Path
from unittest.mock import patch

from arachna.domain.formatter import (
    _apply_repo_map_to_section,
    _format_sigs_json,
    _format_sigs_markdown,
    _format_sigs_xml,
    _generate_header,
    _lang_from_shebang,
    _parse_python,
    _should_skip_binary,
    format_file_section,
)

# ── Shebang edge cases ──────────────────────────────────────────


def test_lang_from_shebang_env_no_args():
    """Shebang with env but no interpreter returns empty string."""
    assert _lang_from_shebang("#!/usr/bin/env") == ""


def test_lang_from_shebang_env_only():
    """Shebang with env and space only."""
    assert _lang_from_shebang("#!/usr/bin/env ") == ""


# ── _should_skip_binary remaining branches ─────────────────────


def test_should_skip_binary_extensions_not_none_ext_not_in(tmp_path):
    """binary_extensions is not None and extension not in list -> skip."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00")
    assert _should_skip_binary(f, True, [".png"], 1.0)


def test_should_skip_binary_include_false_with_os_error(tmp_path):
    """OSError on stat with include_binary=False -> skip."""
    f = tmp_path / "gone.bin"
    f.write_bytes(b"\x00")
    f.unlink()
    assert _should_skip_binary(f, False, None, 1.0)


# ── format_file_section verbose branches ───────────────────────


def test_format_file_section_verbose_binary_too_large(tmp_path, capsys):
    """Verbose output for binary too large."""
    f = tmp_path / "large.bin"
    f.write_bytes(b"\x00" * 2000)
    result = format_file_section(f, include_binary=True, binary_max_mb=0.001, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "too large" in captured.out


def test_format_file_section_verbose_binary_not_in_allowlist(tmp_path, capsys):
    """Verbose output for binary not in allowed extensions."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = format_file_section(
        f, include_binary=True, binary_extensions=[".png"], binary_max_mb=1.0, verbose=True
    )
    captured = capsys.readouterr()
    assert result == ""
    assert "not in allowlist" in captured.out


def test_format_file_section_verbose_file_too_large(tmp_path, capsys):
    """Verbose output for file exceeding ARACHNA_MAX_FILE_SIZE."""
    f = tmp_path / "huge.py"
    f.write_text("x" * 200)
    with patch("arachna.domain.format_output._ARACHNA_MAX_FILE_SIZE", 50):
        result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "too large" in captured.out


def test_format_file_section_verbose_os_error(tmp_path, capsys):
    """Verbose output for OSError on stat."""
    f = tmp_path / "gone.py"
    f.write_text("x")
    f.unlink()
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (error)" in captured.out


def test_format_file_section_unicode_decode_no_binary(tmp_path, capsys):
    """UnicodeDecodeError without include_binary prints verbose skip."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (binary)" in captured.out


def test_format_file_section_permission_error_no_verbose(tmp_path):
    """PermissionError without verbose returns empty string silently."""
    f = tmp_path / "secret.py"
    f.write_text("secret")

    def failing_read_text(*args, **kwargs):
        raise PermissionError("Denied")

    with patch("pathlib.Path.read_text", failing_read_text):
        result = format_file_section(f, verbose=False)
    assert result == ""


def test_format_file_section_os_error_no_verbose(tmp_path):
    """OSError on read without verbose returns empty string silently."""
    f = tmp_path / "error.py"
    f.write_text("x")

    def failing_read_text(*args, **kwargs):
        raise OSError("IO error")

    with patch("pathlib.Path.read_text", failing_read_text):
        result = format_file_section(f, verbose=False)
    assert result == ""


def test_format_file_section_null_bytes_no_binary(tmp_path):
    """Null bytes in text, include_binary=False -> returns empty string."""
    f = tmp_path / "mixed.bin"
    f.write_bytes(b"text\x00binary")
    result = format_file_section(f, include_binary=False)
    assert result == ""


# ── _parse_python SyntaxError fallback ─────────────────────────


def test_parse_python_syntax_error_with_multiline_import():
    """SyntaxError fallback handles multiline imports."""
    text = "import (\n    os,\n    sys\n)\ndef foo(:\n    pass\n"
    deps, exports = _parse_python(text)
    assert "os" in deps
    assert "sys" in deps


def test_parse_python_syntax_error_no_imports():
    """SyntaxError fallback with no imports."""
    text = "def foo(:\n    pass\n"
    deps, exports = _parse_python(text)
    assert deps == []
    assert exports == []


# ── _apply_repo_map_to_section edge cases ──────────────────────


def test_apply_repo_map_to_section_raw_text_none():
    """_apply_repo_map_to_section with raw_text=None returns section unchanged."""
    section = "### test.py\n\n```python\ncode\n```\n"
    result = _apply_repo_map_to_section(Path("test.py"), section, None, "python", "markdown", False)
    assert result == section


def test_apply_repo_map_to_section_include_header_true(tmp_path):
    """_apply_repo_map_to_section with include_header=True adds header."""
    f = tmp_path / "test.py"
    text = "import os\n\ndef foo():\n    return 1\n"
    section = f"### {f}\n\n```python\n{text}\n```\n"
    result = _apply_repo_map_to_section(f, section, text, "python", "markdown", True)
    assert "deps:" in result
    assert "os" in result


def test_apply_repo_map_to_section_json_format(tmp_path):
    """_apply_repo_map_to_section with json format."""
    f = tmp_path / "test.py"
    text = "def foo():\n    pass\n"
    section = f"### {f}\n\n```python\n{text}\n```\n"
    result = _apply_repo_map_to_section(f, section, text, "python", "json", False)
    assert '"path"' in result


def test_apply_repo_map_to_section_xml_format(tmp_path):
    """_apply_repo_map_to_section with xml format."""
    f = tmp_path / "test.py"
    text = "def foo():\n    pass\n"
    section = f"### {f}\n\n```python\n{text}\n```\n"
    result = _apply_repo_map_to_section(f, section, text, "python", "xml", False)
    assert '<file path="' in result


# ── SIGS formatters direct coverage ────────────────────────────


def test_format_sigs_markdown_no_lang(tmp_path):
    """_format_sigs_markdown without language."""
    f = tmp_path / "script"
    result = _format_sigs_markdown(f, "", "function main()")
    assert "```" in result
    assert "```python" not in result


def test_format_sigs_xml_no_lang(tmp_path):
    """_format_sigs_xml without language."""
    f = tmp_path / "script"
    result = _format_sigs_xml(f, "", "function main()")
    assert '<file path="' in result
    assert "language=" not in result


def test_format_sigs_json_no_lang(tmp_path):
    """_format_sigs_json without language."""
    f = tmp_path / "script"
    result = _format_sigs_json(f, "", "function main()")
    data = json.loads(result)
    assert "language" not in data
    assert data["path"] == str(f)


# ── _generate_header with unknown language ─────────────────────


def test_generate_header_unknown_language(tmp_path):
    """_generate_header with unknown language returns empty string."""
    f = tmp_path / "data.xyz"
    text = "some content"
    header = _generate_header(f, text, "unknown_lang")
    assert header == ""
