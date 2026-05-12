import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.gatherer import _collect_named_sections


def test_collect_sections_incremental_new_files():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "a.py").write_text("new file")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("pathlib.Path.cwd", return_value=Path(d)):
                sections, cache = _collect_named_sections(
                    {"directories": [d], "patterns": ["*.py"], "use_gitignore": False},
                    exclude=[],
                    incremental=True,
                    cache={},
                )
                assert len(sections) == 1
                assert len(cache) > 0
        finally:
            os.chdir(wd)


def test_collect_sections_incremental_skips_unchanged():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "a.py").write_text("unchanged")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("pathlib.Path.cwd", return_value=Path(d)):
                # First run
                sections1, cache = _collect_named_sections(
                    {"directories": [d], "patterns": ["*.py"], "use_gitignore": False},
                    exclude=[],
                    incremental=True,
                    cache={},
                )
                assert len(sections1) == 1

                # Second run with same cache
                sections2, cache2 = _collect_named_sections(
                    {"directories": [d], "patterns": ["*.py"], "use_gitignore": False},
                    exclude=[],
                    incremental=True,
                    cache=cache,
                )
                assert len(sections2) == 0
        finally:
            os.chdir(wd)


def test_collect_sections_incremental_detects_modified():
    with tempfile.TemporaryDirectory() as d:
        fp = Path(d) / "a.py"
        fp.write_text("original")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("pathlib.Path.cwd", return_value=Path(d)):
                # First run
                sections1, cache = _collect_named_sections(
                    {"directories": [d], "patterns": ["*.py"], "use_gitignore": False},
                    exclude=[],
                    incremental=True,
                    cache={},
                )
                assert len(sections1) == 1

                # Modify file
                fp.write_text("modified")

                # Second run
                sections2, cache2 = _collect_named_sections(
                    {"directories": [d], "patterns": ["*.py"], "use_gitignore": False},
                    exclude=[],
                    incremental=True,
                    cache=cache,
                )
                assert len(sections2) == 1
        finally:
            os.chdir(wd)
