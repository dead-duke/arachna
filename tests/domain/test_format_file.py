"""Tests for format_file_section — text, binary, shebang, edge cases."""

import json
import sys
from pathlib import Path

import pytest

from arachna.domain.formatting.formatter import (
    _apply_repo_map_to_section,
    _format_sigs_json,
    _format_sigs_markdown,
    _format_sigs_xml,
    _generate_header,
    _is_binary_allowed,
    _lang_from_shebang,
    _parse_python,
    _should_skip_binary,
    format_file_section,
    lang_for_path,
)


def test_python_file(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("print('hello')")
    r = format_file_section(f)
    assert "```python" in r
    assert "print('hello')" in r


def test_empty_file(tmp_path):
    f = tmp_path / "empty.py"
    f.write_text("")
    assert format_file_section(f) != ""


def test_markdown(tmp_path):
    f = tmp_path / "README.md"
    f.write_text("# Hello")
    assert "```markdown" in format_file_section(f)


def test_nonexistent():
    assert format_file_section(Path("/nonexistent")) == ""


def test_no_extension(tmp_path):
    f = tmp_path / "Dockerfile"
    f.write_text("FROM python:3.11")
    assert "```dockerfile" in format_file_section(f)


@pytest.mark.skipif(sys.platform == "win32", reason="chmod 0o000 does not work on Windows")
def test_permission_denied(tmp_path):
    f = tmp_path / "secret.py"
    f.write_text("s")
    f.chmod(0o000)
    assert format_file_section(f) == ""
    f.chmod(0o644)


def test_binary_skipped(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    assert format_file_section(f) == ""


def test_os_error_stat(tmp_path):
    f = tmp_path / "gone.py"
    f.write_text("x")
    f.unlink()
    assert format_file_section(f) == ""


def test_unicode_decode_error(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(f, include_binary=False)
    assert result == ""


def test_unicode_decode_error_binary_included(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(f, include_binary=True, binary_extensions=[".bin"])
    assert "```base64" in result


def test_null_bytes_in_text(tmp_path):
    f = tmp_path / "data.txt"
    f.write_bytes(b"text\x00more")
    result = format_file_section(f)
    assert result == ""


def test_null_bytes_binary_included(tmp_path):
    f = tmp_path / "data.txt"
    f.write_bytes(b"text\x00more")
    result = format_file_section(f, include_binary=True, binary_extensions=[".txt"])
    assert "```base64" in result


def test_lang_from_shebang_python():
    assert _lang_from_shebang("#!/usr/bin/env python3") == "python"


def test_lang_from_shebang_bash():
    assert _lang_from_shebang("#!/bin/bash") == "bash"


def test_lang_from_shebang_no_shebang():
    assert _lang_from_shebang("just text") == ""


def test_lang_from_shebang_empty():
    assert _lang_from_shebang("") == ""


def test_lang_from_shebang_env_only():
    assert _lang_from_shebang("#!/usr/bin/env") == ""


def test_should_skip_binary_nonexistent():
    assert _should_skip_binary(Path("/nonexistent"), True, None, 1.0)


def test_should_skip_binary_not_in_extensions(tmp_path):
    f = tmp_path / "test.xyz"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".bin"], 1.0)


def test_is_binary_allowed_nonexistent(tmp_path):
    assert not _is_binary_allowed(tmp_path / "nope.bin", None, 1.0)


def test_is_binary_allowed_too_large(tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * 2000)
    assert not _is_binary_allowed(f, [".bin"], 0.001)


def test_is_binary_allowed_wrong_extension(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert not _is_binary_allowed(f, [".png"], 1.0)


def test_is_binary_allowed_ok(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert _is_binary_allowed(f, [".bin"], 1.0)


def test_lang_for_path_unknown():
    assert lang_for_path(Path("data.xyz")) == ""


def test_lang_for_path_dockerfile_uppercase():
    assert lang_for_path(Path("DOCKERFILE")) == "dockerfile"


# Edge cases from test_formatter_edge.py


def test_lang_from_shebang_env_no_args():
    assert _lang_from_shebang("#!/usr/bin/env") == ""


def test_skip_extensions_not_none_ext_not_in(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00")
    assert _should_skip_binary(f, True, [".png"], 1.0)


def test_skip_include_false_with_os_error(tmp_path):
    f = tmp_path / "gone.bin"
    f.write_bytes(b"\x00")
    f.unlink()
    assert _should_skip_binary(f, False, None, 1.0)


def test_verbose_binary_too_large(tmp_path, capsys):
    f = tmp_path / "large.bin"
    f.write_bytes(b"\x00" * 2000)
    from unittest.mock import patch

    with patch("arachna.domain.formatting.format_output._ARACHNA_MAX_FILE_SIZE", 50):
        result = format_file_section(f, include_binary=True, binary_max_mb=0.001, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "too large" in captured.out


def test_verbose_binary_not_in_allowlist(tmp_path, capsys):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = format_file_section(
        f, include_binary=True, binary_extensions=[".png"], binary_max_mb=1.0, verbose=True
    )
    captured = capsys.readouterr()
    assert result == ""
    assert "not in allowlist" in captured.out


def test_verbose_file_too_large(tmp_path, capsys):
    f = tmp_path / "huge.py"
    f.write_text("x" * 200)
    from unittest.mock import patch

    with patch("arachna.domain.formatting.format_output._ARACHNA_MAX_FILE_SIZE", 50):
        result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "too large" in captured.out


def test_verbose_os_error(tmp_path, capsys):
    f = tmp_path / "gone.py"
    f.write_text("x")
    f.unlink()
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (error)" in captured.out


def test_unicode_decode_no_binary(tmp_path, capsys):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(f, verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "Skipped (binary)" in captured.out


def test_permission_error_no_verbose(tmp_path):
    f = tmp_path / "secret.py"
    f.write_text("secret")
    from unittest.mock import patch

    def failing_read_text(*args, **kwargs):
        raise PermissionError("Denied")

    with patch("pathlib.Path.read_text", failing_read_text):
        result = format_file_section(f, verbose=False)
    assert result == ""


def test_os_error_no_verbose(tmp_path):
    f = tmp_path / "error.py"
    f.write_text("x")
    from unittest.mock import patch

    def failing_read_text(*args, **kwargs):
        raise OSError("IO error")

    with patch("pathlib.Path.read_text", failing_read_text):
        result = format_file_section(f, verbose=False)
    assert result == ""


def test_null_bytes_no_binary(tmp_path):
    f = tmp_path / "mixed.bin"
    f.write_bytes(b"text\x00binary")
    result = format_file_section(f, include_binary=False)
    assert result == ""


def test_unicode_decode_fallback(tmp_path, capsys):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(f, include_binary=True, binary_extensions=[".png"], verbose=True)
    captured = capsys.readouterr()
    assert result == ""
    assert "not in allowlist" in captured.out


def test_parse_python_syntax_error_multiline_import():
    text = "import (\n    os,\n    sys\n)\ndef foo(:\n    pass\n"
    deps, exports = _parse_python(text)
    assert "os" in deps
    assert "sys" in deps


def test_parse_python_syntax_error_no_imports():
    text = "def foo(:\n    pass\n"
    deps, exports = _parse_python(text)
    assert deps == []
    assert exports == []


def test_parse_python_syntax_error_with_from_import():
    text = "from pathlib import Path\ndef foo(:\n    pass\n"
    deps, exports = _parse_python(text)
    assert "pathlib" in deps


def test_repo_map_raw_text_none():
    section = "### test.py\n\n```python\ncode\n```\n"
    result = _apply_repo_map_to_section(Path("test.py"), section, None, "python", "markdown", False)
    assert result == section


def test_repo_map_include_header_true(tmp_path):
    f = tmp_path / "test.py"
    text = "import os\n\ndef foo():\n    return 1\n"
    section = f"### {f}\n\n```python\n{text}\n```\n"
    result = _apply_repo_map_to_section(f, section, text, "python", "markdown", True)
    assert "deps:" in result
    assert "os" in result


def test_repo_map_json_format(tmp_path):
    f = tmp_path / "test.py"
    text = "def foo():\n    pass\n"
    section = f"### {f}\n\n```python\n{text}\n```\n"
    result = _apply_repo_map_to_section(f, section, text, "python", "json", False)
    assert '"path"' in result


def test_repo_map_xml_format(tmp_path):
    f = tmp_path / "test.py"
    text = "def foo():\n    pass\n"
    section = f"### {f}\n\n```python\n{text}\n```\n"
    result = _apply_repo_map_to_section(f, section, text, "python", "xml", False)
    assert '<file path="' in result


def test_sigs_markdown_no_lang(tmp_path):
    f = tmp_path / "script"
    result = _format_sigs_markdown(f, "", "function main()")
    assert "```" in result
    assert "```python" not in result


def test_sigs_xml_no_lang(tmp_path):
    f = tmp_path / "script"
    result = _format_sigs_xml(f, "", "function main()")
    assert '<file path="' in result
    assert "language=" not in result


def test_sigs_json_no_lang(tmp_path):
    f = tmp_path / "script"
    result = _format_sigs_json(f, "", "function main()")
    data = json.loads(result)
    assert "language" not in data
    assert data["path"] == str(f)


def test_header_unknown_language(tmp_path):
    f = tmp_path / "data.xyz"
    text = "some content"
    header = _generate_header(f, text, "unknown_lang")
    assert header == ""
