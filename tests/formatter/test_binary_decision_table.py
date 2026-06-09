"""Coverage for _should_skip_binary decision table branches."""

from arachna.formatter import _should_skip_binary


def test_no_extension_include_binary_false_null_byte(tmp_path):
    """No extension, include_binary=False — checks for null bytes, finds them."""
    f = tmp_path / "noext"
    f.write_bytes(b"\x00\x01")
    assert _should_skip_binary(f, False, None, 1.0)


def test_no_extension_include_binary_false_no_null(tmp_path):
    """No extension, include_binary=False — checks for null bytes, none found."""
    f = tmp_path / "noext"
    f.write_text("plain text")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_no_extension_include_binary_false_os_error(tmp_path):
    """No extension, include_binary=False, file unreadable — skip."""
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, False, None, 1.0)


def test_no_extension_include_binary_true_empty_allowed(tmp_path):
    """No extension, include_binary=True, '' in binary_extensions."""
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [""], 1.0)


def test_no_extension_include_binary_true_not_in_list(tmp_path):
    """No extension, include_binary=True, '' not in binary_extensions."""
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".bin"], 1.0)


def test_no_extension_include_binary_true_extensions_none(tmp_path):
    """No extension, include_binary=True, binary_extensions=None."""
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, None, 1.0)


def test_has_extension_in_text_extensions_not_skipped(tmp_path):
    """File with .py extension never skipped even if include_binary=False."""
    f = tmp_path / "main.py"
    f.write_text("code")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_has_extension_not_in_text_not_in_binary_extensions(tmp_path):
    """Extension not in _TEXT_EXTENSIONS, not in binary_extensions → skip."""
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".bin"], 1.0)


def test_has_extension_in_binary_extensions_include_true(tmp_path):
    """Extension in binary_extensions, include_binary=True → don't skip."""
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [".xyz"], 1.0)


def test_has_extension_not_in_binary_extensions_include_false(tmp_path):
    """Extension not in _TEXT_EXTENSIONS, include_binary=False → skip."""
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, False, None, 1.0)


def test_os_error_on_stat(tmp_path):
    """File that raises OSError on stat → skip."""
    f = tmp_path / "gone.xyz"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, True, None, 1.0)
