import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.gatherer import dry_run


def test_single_file():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "main.py").write_text("print('hello')")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("pathlib.Path.cwd", return_value=Path(d)):
                stats = dry_run(
                    {
                        "directories": [d],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "name_template": "chat",
                    }
                )
        finally:
            os.chdir(wd)
        assert stats["max_tokens"] == 16000
        assert len(stats["parts"]) == 1


def test_multiple_parts():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "a.py").write_text("x" * 500)
        (Path(d) / "b.py").write_text("y" * 500)
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("pathlib.Path.cwd", return_value=Path(d)):
                stats = dry_run(
                    {
                        "directories": [d],
                        "patterns": ["*.py"],
                        "max_tokens": 50,
                        "name_template": "chat",
                    }
                )
        finally:
            os.chdir(wd)
        assert len(stats["parts"]) == 2


def test_empty_dir():
    with tempfile.TemporaryDirectory() as d:
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("pathlib.Path.cwd", return_value=Path(d)):
                stats = dry_run(
                    {
                        "directories": [d],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "name_template": "chat",
                    }
                )
        finally:
            os.chdir(wd)
        assert len(stats["parts"]) == 0


def test_command_mode():
    stats = dry_run({"command": "echo hi", "max_tokens": 16000, "name_template": "chat"})
    assert len(stats["parts"]) == 1


def test_section_too_large():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "big.py").write_text("x" * 400)
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("pathlib.Path.cwd", return_value=Path(d)):
                stats = dry_run(
                    {
                        "directories": [d],
                        "patterns": ["*.py"],
                        "max_tokens": 10,
                        "name_template": "chat",
                    }
                )
        finally:
            os.chdir(wd)
        assert len(stats["parts"]) == 1
        assert stats["parts"][0]["total_tokens"] > 10
