import tempfile
from pathlib import Path

from arachna.gatherer import gather_files


def test_single():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "main.py").write_text("print('hello')")
        sections = gather_files(
            {"directories": [str(root)], "patterns": ["*.py"], "use_gitignore": False},
            root=root,
        )
        assert len(sections) == 1
        assert "main.py" in sections[0]


def test_multiple():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "a.py").write_text("a")
        (root / "b.py").write_text("b")
        sections = gather_files(
            {"directories": [str(root)], "patterns": ["*.py"], "use_gitignore": False},
            root=root,
        )
        assert len(sections) == 2


def test_exclude():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "main.py").write_text("ok")
        (root / "test.pyc").write_text("junk")
        sections = gather_files(
            {
                "directories": [str(root)],
                "patterns": ["*"],
                "exclude_patterns": ["*.pyc"],
                "use_gitignore": False,
            },
            root=root,
        )
        assert len(sections) == 1


def test_specific_files():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "README.md").write_text("# Hi")
        sections = gather_files(
            {"directories": [], "files": [str(root / "README.md")], "use_gitignore": False},
            root=root,
        )
        assert len(sections) == 1


def test_nonexistent_file():
    sections = gather_files({"directories": [], "files": ["/nonexistent"], "use_gitignore": False})
    assert len(sections) == 0


def test_pre_commands():
    sections = gather_files(
        {"pre_commands": ["echo hi"], "directories": [], "use_gitignore": False}
    )
    assert len(sections) == 1


def test_empty_dir():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        sections = gather_files(
            {"directories": [str(root)], "patterns": ["*.py"], "use_gitignore": False},
            root=root,
        )
        assert len(sections) == 0


def test_subdirectory():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "sub").mkdir()
        (root / "sub" / "nested.py").write_text("x")
        sections = gather_files(
            {"directories": [str(root)], "patterns": ["*.py"], "use_gitignore": False},
            root=root,
        )
        assert len(sections) == 1
