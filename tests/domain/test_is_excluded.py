from pathlib import Path

from arachna.domain.formatting.formatter import is_excluded


def test_by_name():
    assert is_excluded(Path("__pycache__/main.pyc"), ["*__pycache__*"])


def test_by_path():
    assert is_excluded(Path("venv/lib/module.py"), ["venv/*"])


def test_by_git():
    assert is_excluded(Path(".git/config"), [".git/*"])


def test_not_excluded():
    assert not is_excluded(Path("src/main.py"), ["*__pycache__*"])
