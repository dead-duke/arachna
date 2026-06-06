"""Edge case tests for formatter.py uncovered branches."""

from pathlib import Path

from arachna.formatter import (
    _is_binary_allowed,
    _should_skip_binary,
    format_file_section,
    lang_for_path,
)


def test_should_skip_binary_text_extension_not_skipped(tmp_path):
    """Known text extension .json is never skipped."""
    f = tmp_path / "config.json"
    f.write_text('{"key": "value"}')
    assert not _should_skip_binary(f, False, None, 1.0)


def test_should_skip_binary_os_error_on_stat(tmp_path):
    """File that raises OSError on stat is skipped."""
    f = tmp_path / "gone.bin"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, True, None, 1.0)


def test_is_binary_allowed_nonexistent(tmp_path):
    """Non-existent file not allowed."""
    assert not _is_binary_allowed(tmp_path / "nope.bin", None, 1.0)


def test_is_binary_allowed_wrong_extension(tmp_path):
    """Wrong extension not allowed."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert not _is_binary_allowed(f, [".png"], 1.0)


def test_is_binary_allowed_too_large(tmp_path):
    """File over size limit not allowed."""
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * 2000)
    assert not _is_binary_allowed(f, [".bin"], 0.001)


def test_is_binary_allowed_ok(tmp_path):
    """Matching extension and size is allowed."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert _is_binary_allowed(f, [".bin"], 1.0)


def test_is_binary_allowed_no_extensions_none(tmp_path):
    """extensions=None allows all."""
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert _is_binary_allowed(f, None, 1.0)


def test_format_file_section_os_error_on_stat(tmp_path):
    """File that disappears between checks returns empty."""
    f = tmp_path / "ghost.py"
    f.write_text("x")
    f.unlink()
    result = format_file_section(f, verbose=False)
    assert result == ""


def test_format_file_section_no_extension_text(tmp_path):
    """No-extension file treated as text, formatted without language."""
    f = tmp_path / "Makefile"
    f.write_text("all:\n\techo hi")
    result = format_file_section(f)
    assert "```makefile" in result


def test_lang_for_path_case_insensitive():
    """Filename matching is case-insensitive."""
    assert lang_for_path(Path("Dockerfile")) == "dockerfile"
    assert lang_for_path(Path("DOCKERFILE")) == "dockerfile"
    assert lang_for_path(Path("Makefile")) == "makefile"


def test_should_skip_binary_no_extension_include_true(tmp_path):
    """No extension + include_binary=True + extensions=None → not skipped."""
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, None, 1.0)


def test_should_skip_binary_no_extension_include_false(tmp_path):
    """No extension + include_binary=False → not skipped (treated as text)."""
    f = tmp_path / "noext"
    f.write_text("text content")
    assert not _should_skip_binary(f, False, None, 1.0)
