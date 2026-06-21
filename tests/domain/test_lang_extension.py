from pathlib import Path

from arachna.domain.formatting.formatter import lang_for_path


def test_py():
    assert lang_for_path(Path("main.py")) == "python"


def test_json():
    assert lang_for_path(Path("config.json")) == "json"


def test_toml():
    assert lang_for_path(Path("pyproject.toml")) == "toml"


def test_md():
    assert lang_for_path(Path("README.md")) == "markdown"


def test_sh():
    assert lang_for_path(Path("script.sh")) == "bash"


def test_css():
    assert lang_for_path(Path("style.css")) == "css"
