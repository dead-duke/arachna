import os
import tempfile
from pathlib import Path

from arachna.collector import collect


def test_single_file():
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hi')")
        out = Path(d) / "out"
        out.mkdir()
        wd = os.getcwd()
        os.chdir(d)
        try:
            created = collect(
                {
                    "name_template": "c",
                    "title_template": "# T (part {part})\n\n",
                    "max_tokens": 16000,
                    "split_mode": "by_file",
                    "directories": ["src"],
                    "patterns": ["*.py"],
                },
                "P",
                "out",
            )
        finally:
            os.chdir(wd)
        assert len(created) == 1
        assert "c.md" in created[0]


def test_multiple_parts():
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "src"
        src.mkdir()
        (src / "a.py").write_text("x" * 2000)
        (src / "b.py").write_text("y" * 2000)
        out = Path(d) / "out"
        out.mkdir()
        wd = os.getcwd()
        os.chdir(d)
        try:
            created = collect(
                {
                    "name_template": "c",
                    "title_template": "# T (part {part})\n\n",
                    "max_tokens": 10,
                    "split_mode": "by_file",
                    "directories": ["src"],
                    "patterns": ["*.py"],
                },
                "P",
                "out",
            )
        finally:
            os.chdir(wd)
        assert len(created) == 2


def test_empty():
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "src"
        src.mkdir()
        out = Path(d) / "out"
        out.mkdir()
        wd = os.getcwd()
        os.chdir(d)
        try:
            created = collect(
                {
                    "name_template": "c",
                    "title_template": "# T (part {part})\n\n",
                    "max_tokens": 16000,
                    "split_mode": "by_file",
                    "directories": ["src"],
                    "patterns": ["*.py"],
                },
                "P",
                "out",
            )
        finally:
            os.chdir(wd)
        assert len(created) == 0


def test_command_mode():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "out"
        out.mkdir()
        wd = os.getcwd()
        os.chdir(d)
        try:
            created = collect(
                {
                    "name_template": "c",
                    "title_template": "# T (part {part})\n\n",
                    "max_tokens": 16000,
                    "split_mode": "by_paragraph",
                    "command": "echo hi",
                },
                "P",
                "out",
            )
        finally:
            os.chdir(wd)
        assert len(created) == 1
