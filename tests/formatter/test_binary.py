import tempfile
from pathlib import Path

from arachna.formatter import format_file_section


def test_binary_skipped_by_default():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        result = format_file_section(f)
        assert result == ""


def test_binary_included_when_enabled():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        result = format_file_section(
            f, include_binary=True, binary_extensions=[".bin"], binary_max_mb=1.0
        )
        assert "```base64" in result


def test_binary_skipped_wrong_extension():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        result = format_file_section(
            f, include_binary=True, binary_extensions=[".png"], binary_max_mb=1.0
        )
        assert result == ""


def test_binary_skipped_too_large():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data.bin"
        f.write_bytes(b"\x00" * 2000)
        result = format_file_section(
            f, include_binary=True, binary_extensions=[".bin"], binary_max_mb=0.001
        )
        assert result == ""
