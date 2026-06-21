import json
import tempfile
from pathlib import Path

from arachna.domain.formatting.formatter import format_file_section


def test_format_json_python():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "test.py"
        f.write_text("print('hello')")
        result = format_file_section(f, fmt="json")
        data = json.loads(result)
        assert data["path"] == str(f)
        assert data["language"] == "python"
        assert data["content"] == "print('hello')"


def test_format_json_no_language():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "script"
        f.write_text("just text")
        result = format_file_section(f, fmt="json")
        data = json.loads(result)
        assert data["path"] == str(f)
        assert "language" not in data
