import json
import tempfile
from pathlib import Path

from arachna.domain.formatter import format_file_section


def test_binary_skipped_by_default():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        result = format_file_section(f)
        assert result == ""


def test_binary_included_markdown():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        result = format_file_section(
            f, include_binary=True, binary_extensions=[".bin"], binary_max_mb=1.0
        )
        assert "```base64" in result


def test_binary_included_xml():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        result = format_file_section(
            f, fmt="xml", include_binary=True, binary_extensions=[".bin"], binary_max_mb=1.0
        )
        assert 'encoding="base64"' in result
        assert "<file" in result


def test_binary_included_json():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        result = format_file_section(
            f, fmt="json", include_binary=True, binary_extensions=[".bin"], binary_max_mb=1.0
        )
        data = json.loads(result)
        assert data["encoding"] == "base64"
        assert data["path"] == str(f)
        assert "language" not in data


def test_binary_json_no_extension():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data"
        f.write_bytes(b"\x00\x01\x02")
        result = format_file_section(
            f, fmt="json", include_binary=True, binary_extensions=[""], binary_max_mb=1.0
        )
        data = json.loads(result)
        assert data["encoding"] == "base64"


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
