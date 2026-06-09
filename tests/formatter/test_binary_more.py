"""Targeted coverage for _should_skip_binary remaining branches."""

from arachna.formatter import _should_skip_binary


def test_too_large_include_binary_true(tmp_path):
    """File over size limit with include_binary=True."""
    f = tmp_path / "big.xyz"
    f.write_bytes(b"x" * 2000)
    assert _should_skip_binary(f, True, [".xyz"], 0.001)


def test_not_in_text_not_in_binary_include_false(tmp_path):
    """Extension not in _TEXT_EXTENSIONS, include_binary=False, binary_extensions set."""
    f = tmp_path / "data.xyz"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, False, [".bin"], 1.0)


def test_in_binary_extensions_include_true_no_size_check_needed(tmp_path):
    """Extension in binary_extensions, include_binary=True, within size limit."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert not _should_skip_binary(f, True, [".bin"], 1.0)


def test_not_in_binary_extensions_include_true(tmp_path):
    """Extension not in binary_extensions, include_binary=True."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"x")
    assert _should_skip_binary(f, True, [".png"], 1.0)
