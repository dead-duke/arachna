import tempfile
from pathlib import Path

from arachna.formatter import format_file_section


def test_python_file():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "test.py"
        f.write_text("print('hello')")
        r = format_file_section(f)
        assert "```python" in r
        assert "print('hello')" in r


def test_empty_file():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "empty.py"
        f.write_text("")
        assert format_file_section(f) != ""


def test_markdown():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "README.md"
        f.write_text("# Hello")
        assert "```markdown" in format_file_section(f)


def test_nonexistent():
    assert format_file_section(Path("/nonexistent")) == ""


def test_no_extension():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "Dockerfile"
        f.write_text("FROM python:3.11")
        assert "```dockerfile" in format_file_section(f)


def test_permission_denied():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "secret.py"
        f.write_text("s")
        f.chmod(0o000)
        assert format_file_section(f) == ""
        f.chmod(0o644)


def test_binary_skipped():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        assert format_file_section(f) == ""
