"""Tests for line_numbers feature in format_file_section."""

from arachna.domain.formatter import _add_line_numbers, format_file_section


def test_add_line_numbers_basic():
    text = "line1\nline2\nline3"
    result = _add_line_numbers(text)
    lines = result.split("\n")
    assert lines[0] == "    1| line1"
    assert lines[1] == "    2| line2"
    assert lines[2] == "    3| line3"


def test_add_line_numbers_empty():
    assert _add_line_numbers("") == ""


def test_add_line_numbers_single_line():
    result = _add_line_numbers("hello")
    assert result == "    1| hello"


def test_add_line_numbers_10000_lines():
    lines = ["line"] * 10000
    text = "\n".join(lines)
    result = _add_line_numbers(text)
    result_lines = result.split("\n")
    assert len(result_lines) == 10000
    assert result_lines[0] == "    1| line"
    assert result_lines[9999] == "10000| line"


def test_format_file_section_markdown_with_line_numbers(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("print('hello')\nprint('world')\n")
    result = format_file_section(f, line_numbers=True)
    assert "```python" in result
    assert "    1| print('hello')" in result
    assert "    2| print('world')" in result


def test_format_file_section_markdown_without_line_numbers(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("print('hello')\nprint('world')\n")
    result = format_file_section(f, line_numbers=False)
    assert "print('hello')" in result
    assert "    1|" not in result


def test_format_file_section_xml_with_line_numbers(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("print('hello')\n")
    result = format_file_section(f, fmt="xml", line_numbers=True)
    assert "<![CDATA[" in result
    assert "    1| print('hello')" in result


def test_format_file_section_json_with_line_numbers(tmp_path):
    import json

    f = tmp_path / "test.py"
    f.write_text("print('hello')\n")
    result = format_file_section(f, fmt="json", line_numbers=True)
    data = json.loads(result)
    assert "    1| print('hello')" in data["content"]


def test_format_file_section_empty_file_with_line_numbers(tmp_path):
    f = tmp_path / "empty.py"
    f.write_text("")
    result = format_file_section(f, line_numbers=True)
    assert result != ""
    assert "```python" in result


def test_format_file_section_default_no_line_numbers(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("print('hello')\n")
    result = format_file_section(f)
    assert "    1|" not in result
