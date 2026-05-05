"""Tests for formatter — language detection, exclusion, file formatting."""

import tempfile
from pathlib import Path

from arachna.formatter import format_file_section, is_excluded, lang_for_path


# lang_for_path
def test_lang_by_extension():
    assert lang_for_path(Path("main.py")) == "python"
    assert lang_for_path(Path("config.json")) == "json"
    assert lang_for_path(Path("pyproject.toml")) == "toml"
    assert lang_for_path(Path("README.md")) == "markdown"
    assert lang_for_path(Path("script.sh")) == "bash"
    assert lang_for_path(Path("style.css")) == "css"


def test_lang_by_filename():
    assert lang_for_path(Path("Dockerfile")) == "dockerfile"
    assert lang_for_path(Path("Makefile")) == "makefile"
    assert lang_for_path(Path(".env")) == "bash"
    assert lang_for_path(Path("Procfile")) == "yaml"


def test_lang_unknown():
    assert lang_for_path(Path("data.bin")) == ""


def test_lang_case_insensitive():
    assert lang_for_path(Path("MAKEFILE")) == "makefile"
    assert lang_for_path(Path("DOCKERFILE")) == "dockerfile"


# is_excluded
def test_is_excluded_by_name():
    assert is_excluded(Path("__pycache__/main.pyc"), ["*__pycache__*"])
    assert is_excluded(Path("src/__pycache__/main.py"), ["*__pycache__*"])
    assert is_excluded(Path("test.pyc"), ["*.pyc"])


def test_is_excluded_by_path():
    assert is_excluded(Path("venv/lib/module.py"), ["venv/*"])
    assert is_excluded(Path(".git/config"), [".git/*"])


def test_is_not_excluded():
    assert not is_excluded(Path("src/main.py"), ["*__pycache__*", "*.pyc"])
    assert not is_excluded(Path("README.md"), [])


# format_file_section
def test_format_file_section_python():
    with tempfile.TemporaryDirectory() as tmpdir:
        f = Path(tmpdir) / "test.py"
        f.write_text("print('hello')")
        result = format_file_section(f)
        assert "### " in result
        assert "test.py" in result
        assert "```python" in result
        assert "print('hello')" in result


def test_format_file_section_empty_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        f = Path(tmpdir) / "empty.py"
        f.write_text("")
        result = format_file_section(f)
        assert result != ""


def test_format_file_section_markdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        f = Path(tmpdir) / "README.md"
        f.write_text("# Hello")
        result = format_file_section(f)
        assert "```markdown" in result
        assert "# Hello" in result


def test_format_file_section_nonexistent():
    result = format_file_section(Path("/nonexistent/file.txt"))
    assert result == ""


def test_format_file_section_no_extension():
    with tempfile.TemporaryDirectory() as tmpdir:
        f = Path(tmpdir) / "Dockerfile"
        f.write_text("FROM python:3.11")
        result = format_file_section(f)
        assert "```dockerfile" in result
        assert "FROM python:3.11" in result


def test_format_file_section_permission_denied():
    with tempfile.TemporaryDirectory() as tmpdir:
        f = Path(tmpdir) / "secret.py"
        f.write_text("secret")
        f.chmod(0o000)
        result = format_file_section(f)
        assert result == ""
        f.chmod(0o644)


def test_format_file_section_binary_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        f = Path(tmpdir) / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        result = format_file_section(f)
        assert result == ""
