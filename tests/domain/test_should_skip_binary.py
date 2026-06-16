"""Tests for _should_skip_binary function."""

from pathlib import Path

from arachna.domain.formatter import _should_skip_binary


def test_nonexistent_file_skipped():
    assert _should_skip_binary(Path("/nonexistent/file.bin"), True, None, 1.0)


def test_file_too_large_skipped(tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * 2000)
    assert _should_skip_binary(f, True, None, 0.001)


def test_wrong_extension_skipped(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".png"], 1.0)


def test_text_file_with_unknown_extension_not_skipped(tmp_path):
    f = tmp_path / "data.bin"
    f.write_text("hello")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_binary_with_null_bytes_skipped(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    assert _should_skip_binary(f, False, None, 1.0)


def test_allowed_binary_not_skipped(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [".bin"], 1.0)


def test_os_error_on_stat(tmp_path):
    f = tmp_path / "gone.bin"
    f.write_bytes(b"x")
    f.unlink()
    assert _should_skip_binary(f, True, None, 1.0)


def test_no_extension_allowed_with_empty_list(tmp_path):
    f = tmp_path / "data"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [""], 1.0)


def test_no_extension_skipped_with_other_list(tmp_path):
    f = tmp_path / "data"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".png"], 1.0)


def test_binary_extensions_none_include_true_not_skipped(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, None, 1.0)


def test_binary_extensions_none_include_false_text_not_skipped(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_text("text")
    assert not _should_skip_binary(f, False, None, 1.0)


def test_binary_extensions_none_include_false_binary_skipped(tmp_path):
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
    f2 = tmp_path / "Makefile"
    f2.write_text("all:")
    assert not _should_skip_binary(f, False, None, 1.0)
    assert not _should_skip_binary(f2, False, None, 1.0)


def test_no_extension_binary_include_true_skipped(tmp_path):
    f = tmp_path / "unknown_binary"
    f.write_bytes(b"\x00\x01\x02")
    assert _should_skip_binary(f, True, [".bin"], 1.0)


def test_no_extension_binary_include_true_allowed(tmp_path):
    f = tmp_path / "unknown_binary"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [""], 1.0)


def test_no_extension_size_check(tmp_path):
    f = tmp_path / "large_noext"
    f.write_bytes(b"x" * 2000)
    assert _should_skip_binary(f, True, None, 0.001)
