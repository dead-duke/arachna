import sys
from pathlib import Path

import pytest

from arachna.formatter import (
    _is_binary_allowed,
    _lang_from_shebang,
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
    """File that raises OSError on stat returns empty string."""
    f = tmp_path / "gone.py"
    f.write_text("x")
    f.unlink()
    assert format_file_section(f) == ""


def test_unicode_decode_error(tmp_path):
    """Non-UTF8 file without binary include returns empty."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(f, include_binary=False)
    assert result == ""


def test_unicode_decode_error_binary_included(tmp_path):
    """Non-UTF8 file with binary include returns base64."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x80\x81\x82")
    result = format_file_section(f, include_binary=True, binary_extensions=[".bin"])
    assert "```base64" in result


def test_null_bytes_in_text(tmp_path):
    """File with null bytes treated as binary."""
    f = tmp_path / "data.txt"
    f.write_bytes(b"text\x00more")
    result = format_file_section(f)
    assert result == ""


def test_null_bytes_binary_included(tmp_path):
    """File with null bytes included as base64 when binary allowed."""
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
    """#!/usr/bin/env with no args returns empty."""
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
