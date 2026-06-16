"""Coverage for _should_skip_binary decision table branches."""

from arachna.domain.formatter import _should_skip_binary


def test_no_extension_include_binary_false_null_byte(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"\x00\x01")
    assert _should_skip_binary(f, False, None, 1.0)


def test_no_extension_include_binary_false_no_null(tmp_path):
    f = tmp_path / "noext"
    f.write_text("plain text")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_no_extension_include_binary_false_os_error(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, False, None, 1.0)


def test_no_extension_include_binary_true_empty_allowed(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [""], 1.0)


def test_no_extension_include_binary_true_not_in_list(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".bin"], 1.0)


def test_no_extension_include_binary_true_extensions_none(tmp_path):
    f = tmp_path / "noext"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, None, 1.0)


def test_has_extension_in_text_extensions_not_skipped(tmp_path):
    f = tmp_path / "main.py"
    f.write_text("code")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_has_extension_not_in_text_not_in_binary_extensions(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"\x00")
    assert _should_skip_binary(f, True, [".bin"], 1.0)


def test_has_extension_in_binary_extensions_include_true(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [".xyz"], 1.0)


def test_has_extension_include_false_text_no_null(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_text("hello")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_has_extension_include_false_binary_with_null(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"\x00")
    assert _should_skip_binary(f, False, None, 1.0)


def test_os_error_on_stat(tmp_path):
    f = tmp_path / "gone.xyz"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, True, None, 1.0)
