"""Tests for binary file skip reason labels."""

from arachna.domain.formatting.format_binary import _skip_reason_label


def test_skip_reason_label_binary(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00")
    assert _skip_reason_label(f, False, None, 1.0) == "binary"


def test_skip_reason_label_too_large(tmp_path):
    f = tmp_path / "large.bin"
    f.write_bytes(b"\x00" * 2000)
    assert _skip_reason_label(f, True, None, 0.001) == "binary too large"


def test_skip_reason_label_not_in_allowlist(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00")
    assert _skip_reason_label(f, True, [".png"], 1.0) == "binary not in allowlist"


def test_skip_reason_label_os_error(tmp_path):
    f = tmp_path / "ghost.bin"
    f.write_bytes(b"x")
    f.unlink()
    assert _skip_reason_label(f, True, None, 1.0) == "binary"
