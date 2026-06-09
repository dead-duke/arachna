"""Direct unit tests for _is_binary_allowed (v2.9.2)."""

from arachna.formatter import _is_binary_allowed


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
