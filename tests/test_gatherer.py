"""Tests for gatherer — dry_run and gather_files."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.gatherer import dry_run, gather_files

# All gather_files tests need use_gitignore=False to avoid loading project's .gitignore
# All dry_run tests mock Path.cwd to isolate from project directory


# gather_files
def test_gather_files_single():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("print('hello')")
        profile = {
            "directories": [tmpdir],
            "patterns": ["*.py"],
            "exclude_patterns": [],
            "use_gitignore": False,
        }
        sections = gather_files(profile)
        assert len(sections) == 1
        assert "main.py" in sections[0]
        assert "print('hello')" in sections[0]


def test_gather_files_multiple():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "a.py").write_text("a")
        (Path(tmpdir) / "b.py").write_text("b")
        profile = {
            "directories": [tmpdir],
            "patterns": ["*.py"],
            "exclude_patterns": [],
            "use_gitignore": False,
        }
        sections = gather_files(profile)
        assert len(sections) == 2


def test_gather_files_exclude():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("ok")
        (Path(tmpdir) / "test.pyc").write_text("junk")
        profile = {
            "directories": [tmpdir],
            "patterns": ["*"],
            "exclude_patterns": ["*.pyc"],
            "use_gitignore": False,
        }
        sections = gather_files(profile)
        assert len(sections) == 1
        assert "main.py" in sections[0]


def test_gather_files_specific_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "README.md").write_text("# Hello")
        profile = {
            "directories": [],
            "files": [str(Path(tmpdir) / "README.md")],
            "exclude_patterns": [],
            "use_gitignore": False,
        }
        sections = gather_files(profile)
        assert len(sections) == 1
        assert "README.md" in sections[0]


def test_gather_files_nonexistent_specific_file():
    profile = {
        "directories": [],
        "files": ["/nonexistent/file.txt"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }
    sections = gather_files(profile)
    assert len(sections) == 0


def test_gather_files_pre_commands():
    profile = {
        "pre_commands": ["echo hello"],
        "directories": [],
        "exclude_patterns": [],
        "use_gitignore": False,
    }
    sections = gather_files(profile)
    assert len(sections) == 1
    assert "hello" in sections[0]


def test_gather_files_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        profile = {
            "directories": [tmpdir],
            "patterns": ["*.py"],
            "exclude_patterns": [],
            "use_gitignore": False,
        }
        sections = gather_files(profile)
        assert len(sections) == 0


def test_gather_files_subdirectory():
    with tempfile.TemporaryDirectory() as tmpdir:
        sub = Path(tmpdir) / "sub"
        sub.mkdir()
        (sub / "nested.py").write_text("x")
        profile = {
            "directories": [tmpdir],
            "patterns": ["*.py"],
            "exclude_patterns": [],
            "use_gitignore": False,
        }
        sections = gather_files(profile)
        assert len(sections) == 1
        assert "nested.py" in sections[0]


# dry_run
def test_dry_run_single_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("print('hello')")
        profile = {
            "directories": [tmpdir],
            "patterns": ["*.py"],
            "max_tokens": 16000,
            "name_template": "chat-code",
        }
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
            stats = dry_run(profile)
        assert stats["max_tokens"] == 16000
        assert len(stats["parts"]) == 1
        assert any("main.py" in s[0] for s in stats["parts"][0]["sections"])


def test_dry_run_multiple_parts_small_limit():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "a.py").write_text("x" * 500)
        (Path(tmpdir) / "b.py").write_text("y" * 500)
        profile = {
            "directories": [tmpdir],
            "patterns": ["*.py"],
            "max_tokens": 50,
            "name_template": "chat-code",
        }
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
            stats = dry_run(profile)
        assert len(stats["parts"]) == 2


def test_dry_run_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        profile = {
            "directories": [tmpdir],
            "patterns": ["*.py"],
            "max_tokens": 16000,
            "name_template": "chat-code",
        }
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
            stats = dry_run(profile)
        assert len(stats["parts"]) == 0


def test_dry_run_command_mode():
    profile = {
        "command": "echo hello",
        "max_tokens": 16000,
        "name_template": "chat-git",
    }
    stats = dry_run(profile)
    assert len(stats["parts"]) == 1
    section_names = [s[0] for s in stats["parts"][0]["sections"]]
    assert any("command output" in n for n in section_names)


def test_dry_run_excluded_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("print('hello')")
        (Path(tmpdir) / "test.pyc").write_text("junk")
        profile = {
            "directories": [tmpdir],
            "patterns": ["*"],
            "exclude_patterns": ["*.pyc"],
            "max_tokens": 16000,
            "name_template": "chat-code",
        }
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
            stats = dry_run(profile)
        section_names = [s[0] for part in stats["parts"] for s in part["sections"]]
        assert any("main.py" in n for n in section_names)
        assert not any("test.pyc" in n for n in section_names)


def test_dry_run_pre_commands():
    profile = {
        "pre_commands": ["echo pre_output"],
        "directories": [],
        "max_tokens": 16000,
        "name_template": "chat-code",
    }
    stats = dry_run(profile)
    section_names = [s[0] for part in stats["parts"] for s in part["sections"]]
    assert any("pre_output" in n for n in section_names)


def test_dry_run_nonexistent_directory():
    profile = {
        "directories": ["/nonexistent/path/xyz"],
        "patterns": ["*.py"],
        "max_tokens": 16000,
        "name_template": "chat-code",
    }
    stats = dry_run(profile)
    assert len(stats["parts"]) == 0


def test_dry_run_section_too_large_own_part():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "big.py").write_text("x" * 400)
        profile = {
            "directories": [tmpdir],
            "patterns": ["*.py"],
            "max_tokens": 10,
            "name_template": "chat-code",
        }
        with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
            stats = dry_run(profile)
        assert len(stats["parts"]) == 1
        assert stats["parts"][0]["total_tokens"] > 10


def test_gather_files_verbose_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("ok")
        (Path(tmpdir) / "test.pyc").write_text("junk")
        profile = {
            "directories": [tmpdir],
            "patterns": ["*"],
            "exclude_patterns": ["*.pyc"],
            "use_gitignore": False,
        }
        sections = gather_files(profile, verbose=True)
        assert len(sections) == 1


def test_gather_files_verbose_missing_file():
    profile = {
        "directories": [],
        "files": ["/nonexistent/x.txt"],
        "exclude_patterns": [],
        "use_gitignore": False,
    }
    sections = gather_files(profile, verbose=True)
    assert len(sections) == 0
