"""Tests for binary file handling — _should_skip_binary, _is_binary_allowed, format_file_section."""

import json
from pathlib import Path

from arachna.domain.formatting.formatter import (
    _is_binary_allowed,
    _should_skip_binary,
    format_file_section,
)

# -- format_file_section integration tests --


def test_binary_skipped_by_default(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    assert format_file_section(f) == ""


def test_binary_included_markdown(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = format_file_section(
        f, include_binary=True, binary_extensions=[".bin"], binary_max_mb=1.0
    )
    assert "```base64" in result


def test_binary_included_xml(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = format_file_section(
        f, fmt="xml", include_binary=True, binary_extensions=[".bin"], binary_max_mb=1.0
    )
    assert 'encoding="base64"' in result
    assert "<file" in result


def test_binary_included_json(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = format_file_section(
        f, fmt="json", include_binary=True, binary_extensions=[".bin"], binary_max_mb=1.0
    )
    data = json.loads(result)
    assert data["encoding"] == "base64"
    assert data["path"] == str(f)
    assert "language" not in data


def test_binary_json_no_extension(tmp_path):
    f = tmp_path / "data"
    f.write_bytes(b"\x00\x01\x02")
    result = format_file_section(
        f, fmt="json", include_binary=True, binary_extensions=[""], binary_max_mb=1.0
    )
    data = json.loads(result)
    assert data["encoding"] == "base64"


def test_binary_skipped_wrong_extension(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    result = format_file_section(
        f, include_binary=True, binary_extensions=[".png"], binary_max_mb=1.0
    )
    assert result == ""


def test_binary_skipped_too_large(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00" * 2000)
    result = format_file_section(
        f, include_binary=True, binary_extensions=[".bin"], binary_max_mb=0.001
    )
    assert result == ""


# -- _should_skip_binary unit tests --


def test_skip_nonexistent_file():
    assert _should_skip_binary(Path("/nonexistent/file.bin"), True, None, 1.0)


def test_skip_file_too_large(tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * 2000)
    assert _should_skip_binary(f, True, None, 0.001)


def test_skip_wrong_extension(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".png"], 1.0)


def test_skip_os_error_on_stat(tmp_path):
    f = tmp_path / "gone.bin"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, True, None, 1.0)


def test_allow_text_file_unknown_extension(tmp_path):
    f = tmp_path / "data.bin"
    f.write_text("hello")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_skip_binary_null_bytes(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    assert _should_skip_binary(f, False, None, 1.0)


def test_allow_binary_in_allowlist(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [".bin"], 1.0)


def test_allow_no_extension_empty_allowlist(tmp_path):
    f = tmp_path / "data"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [""], 1.0)


def test_skip_no_extension_other_allowlist(tmp_path):
    f = tmp_path / "data"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".png"], 1.0)


def test_allow_extensions_none_include_true(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, None, 1.0)


def test_allow_extensions_none_include_false_text(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_text("text")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_skip_extensions_none_include_false_binary(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"\x00")
    assert _should_skip_binary(f, False, None, 1.0)


def test_text_extension_never_skipped(tmp_path):
    f = tmp_path / "main.py"
    f.write_text("print('hello')")
    assert not _should_skip_binary(f, False, None, 1.0)
    assert not _should_skip_binary(f, True, [".png"], 1.0)


def test_no_extension_text_file_not_skipped(tmp_path):
    f = tmp_path / "Dockerfile"
    f.write_text("FROM python:3.11")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_skip_no_extension_binary_wrong_allowlist(tmp_path):
    f = tmp_path / "unknown_binary"
    f.write_bytes(b"\x00\x01\x02")
    assert _should_skip_binary(f, True, [".bin"], 1.0)


def test_allow_no_extension_binary_empty_allowlist(tmp_path):
    f = tmp_path / "unknown_binary"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [""], 1.0)


def test_skip_no_extension_too_large(tmp_path):
    f = tmp_path / "large_noext"
    f.write_bytes(b"x" * 2000)
    assert _should_skip_binary(f, True, None, 0.001)


def test_skip_no_extension_include_false_null_byte(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"\x00\x01")
    assert _should_skip_binary(f, False, None, 1.0)


def test_allow_no_extension_include_false_no_null(tmp_path):
    f = tmp_path / "noext"
    f.write_text("plain text")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_skip_no_extension_include_false_os_error(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, False, None, 1.0)


def test_allow_no_extension_include_true_empty_allowed(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [""], 1.0)


def test_skip_no_extension_include_true_not_in_list(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".bin"], 1.0)


def test_allow_no_extension_include_true_extensions_none(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, None, 1.0)


def test_allow_has_extension_in_text_extensions(tmp_path):
    f = tmp_path / "main.py"
    f.write_text("code")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_skip_has_extension_not_in_text_not_in_binary(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"\x00")
    assert _should_skip_binary(f, True, [".bin"], 1.0)


def test_allow_has_extension_in_binary_include_true(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [".xyz"], 1.0)


def test_allow_has_extension_include_false_text_no_null(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_text("hello")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_skip_has_extension_include_false_binary_with_null(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"\x00")
    assert _should_skip_binary(f, False, None, 1.0)


def test_skip_os_error_on_stat_include_true(tmp_path):
    f = tmp_path / "gone.xyz"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, True, None, 1.0)


def test_skip_too_large_include_binary_true(tmp_path):
    f = tmp_path / "big.xyz"
    f.write_bytes(b"x" * 2000)
    assert _should_skip_binary(f, True, [".xyz"], 0.001)


def test_skip_not_in_text_not_in_binary_include_false(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, False, [".bin"], 1.0)


def test_allow_in_binary_extensions_include_true(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [".bin"], 1.0)


def test_skip_not_in_binary_extensions_include_true(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".png"], 1.0)


# -- _is_binary_allowed unit tests --


def test_is_binary_allowed_ok(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert _is_binary_allowed(f, [".bin"], 1.0)


def test_is_binary_allowed_nonexistent(tmp_path):
    assert not _is_binary_allowed(tmp_path / "ghost.bin", None, 1.0)


def test_is_binary_allowed_wrong_extension(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert not _is_binary_allowed(f, [".png"], 1.0)


def test_is_binary_allowed_too_large(tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * 2000)
    assert not _is_binary_allowed(f, [".bin"], 0.001)


def test_is_binary_allowed_extensions_none(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert _is_binary_allowed(f, None, 1.0)


def test_is_binary_allowed_extensions_empty(tmp_path):
    f = tmp_path / "data"
    f.write_bytes(b"x")
    assert not _is_binary_allowed(f, [".bin"], 1.0)
