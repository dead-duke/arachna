"""Coverage for formatter.py uncovered branches."""

import json
from pathlib import Path

from arachna.domain.formatting.formatter import (
    _format_binary,
    _format_json,
    _format_markdown,
    _format_xml,
    _is_binary_allowed,
    _lang_from_shebang,
    _should_skip_binary,
    format_file_section,
    lang_for_path,
)


def test_format_binary_xml(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = _format_binary(f, "xml")
    assert '<file path="' in result
    assert 'encoding="base64"' in result
    assert 'extension="bin"' in result


def test_format_binary_json(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = _format_binary(f, "json")
    data = json.loads(result)
    assert data["encoding"] == "base64"
    assert data["path"] == str(f)


def test_format_binary_markdown(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = _format_binary(f, "markdown")
    assert "```base64" in result


def test_format_markdown_no_lang(tmp_path):
    f = tmp_path / "script"
    result = _format_markdown(f, "", "just text")
    assert str(f) in result
    assert "```" in result
    assert "just text" in result


def test_format_xml_no_lang(tmp_path):
    f = tmp_path / "script"
    result = _format_xml(f, "", "just text")
    assert '<file path="' in result
    assert "language=" not in result
    assert "<![CDATA[" in result


def test_format_json_no_lang(tmp_path):
    f = tmp_path / "script"
    result = _format_json(f, "", "just text")
    data = json.loads(result)
    assert data["path"] == str(f)
    assert "language" not in data


def test_lang_from_shebang_env_ruby():
    assert _lang_from_shebang("#!/usr/bin/env ruby") == "ruby"


def test_lang_from_shebang_env_perl():
    assert _lang_from_shebang("#!/usr/bin/env perl") == "perl"


def test_lang_from_shebang_usr_bin_python():
    assert _lang_from_shebang("#!/usr/bin/python") == "python"


def test_format_file_section_nonexistent_no_verbose():
    result = format_file_section(Path("/nonexistent/file.py"))
    assert result == ""


def test_format_file_section_binary_too_large_no_verbose(tmp_path):
    f = tmp_path / "large.bin"
    f.write_bytes(b"\x00" * 2000)
    result = format_file_section(f, include_binary=True, binary_max_mb=0.001)
    assert result == ""


def test_should_skip_binary_text_extension_not_skipped(tmp_path):
    f = tmp_path / "config.json"
    f.write_text('{"key": "value"}')
    assert not _should_skip_binary(f, False, None, 1.0)


def test_should_skip_binary_os_error_on_stat(tmp_path):
    f = tmp_path / "gone.bin"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, True, None, 1.0)


def test_is_binary_allowed_nonexistent(tmp_path):
    assert not _is_binary_allowed(tmp_path / "nope.bin", None, 1.0)


def test_is_binary_allowed_wrong_extension(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert not _is_binary_allowed(f, [".png"], 1.0)


def test_is_binary_allowed_too_large(tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * 2000)
    assert not _is_binary_allowed(f, [".bin"], 0.001)


def test_is_binary_allowed_ok(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert _is_binary_allowed(f, [".bin"], 1.0)


def test_is_binary_allowed_no_extensions_none(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert _is_binary_allowed(f, None, 1.0)


def test_format_file_section_os_error_on_stat(tmp_path):
    f = tmp_path / "ghost.py"
    f.write_text("x")
    f.unlink()
    result = format_file_section(f, verbose=False)
    assert result == ""


def test_format_file_section_no_extension_text(tmp_path):
    f = tmp_path / "Makefile"
    f.write_text("all:\n\techo hi")
    result = format_file_section(f)
    assert "```makefile" in result


def test_lang_for_path_case_insensitive():
    assert lang_for_path(Path("Dockerfile")) == "dockerfile"
    assert lang_for_path(Path("DOCKERFILE")) == "dockerfile"
    assert lang_for_path(Path("Makefile")) == "makefile"


def test_should_skip_binary_no_extension_include_true(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, None, 1.0)


def test_should_skip_binary_no_extension_include_false(tmp_path):
    f = tmp_path / "noext"
    f.write_text("text content")
    assert not _should_skip_binary(f, False, None, 1.0)
