"""Coverage for formatter.py uncovered branches."""

import json
from pathlib import Path

from arachna.formatter import (
    _format_binary,
    _format_json,
    _format_markdown,
    _format_xml,
    _lang_from_shebang,
    format_file_section,
)


def test_format_binary_xml(tmp_path):
    """_format_binary produces XML with encoding="base64"."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = _format_binary(f, "xml")
    assert '<file path="' in result
    assert 'encoding="base64"' in result
    assert 'extension="bin"' in result


def test_format_binary_json(tmp_path):
    """_format_binary produces JSON with encoding base64."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = _format_binary(f, "json")
    data = json.loads(result)
    assert data["encoding"] == "base64"
    assert data["path"] == str(f)


def test_format_binary_markdown(tmp_path):
    """_format_binary produces markdown with base64 code fence."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = _format_binary(f, "markdown")
    assert "```base64" in result


def test_format_markdown_no_lang(tmp_path):
    """_format_markdown with empty lang produces code fence without language."""
    f = tmp_path / "script"
    result = _format_markdown(f, "", "just text")
    assert str(f) in result
    assert "```" in result
    assert "just text" in result


def test_format_xml_no_lang(tmp_path):
    """_format_xml with empty lang produces file tag without language attr."""
    f = tmp_path / "script"
    result = _format_xml(f, "", "just text")
    assert '<file path="' in result
    assert "language=" not in result
    assert "<![CDATA[" in result


def test_format_json_no_lang(tmp_path):
    """_format_json with empty lang produces JSON without language key."""
    f = tmp_path / "script"
    result = _format_json(f, "", "just text")
    data = json.loads(result)
    assert data["path"] == str(f)
    assert "language" not in data


def test_lang_from_shebang_env_ruby():
    """Shebang with env ruby detected as ruby."""
    assert _lang_from_shebang("#!/usr/bin/env ruby") == "ruby"


def test_lang_from_shebang_env_perl():
    """Shebang with env perl detected as perl."""
    assert _lang_from_shebang("#!/usr/bin/env perl") == "perl"


def test_lang_from_shebang_usr_bin_python():
    """Shebang with /usr/bin/python detected as python."""
    assert _lang_from_shebang("#!/usr/bin/python") == "python"


def test_format_file_section_nonexistent_no_verbose():
    """Non-existent file returns empty without crash in non-verbose."""
    result = format_file_section(Path("/nonexistent/file.py"))
    assert result == ""


def test_format_file_section_binary_too_large_no_verbose(tmp_path):
    """Binary file over limit returns empty in non-verbose mode."""
    f = tmp_path / "large.bin"
    f.write_bytes(b"\x00" * 2000)
    result = format_file_section(f, include_binary=True, binary_max_mb=0.001)
    assert result == ""
