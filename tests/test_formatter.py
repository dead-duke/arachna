"""Tests for formatter — language detection and exclusion."""

from pathlib import Path

from arachna.formatter import lang_for_path, is_excluded


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
