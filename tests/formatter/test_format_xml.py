import tempfile
from pathlib import Path

from arachna.formatter import format_file_section


def test_format_xml_python():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "test.py"
        f.write_text("print('hello')")
        result = format_file_section(f, fmt="xml")
        assert '<file path="' in result
        assert 'language="python"' in result
        assert "<![CDATA[" in result
        assert "print('hello')" in result


def test_format_xml_no_language():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "script"
        f.write_text("just text")
        result = format_file_section(f, fmt="xml")
        assert '<file path="' in result
        assert "language=" not in result
