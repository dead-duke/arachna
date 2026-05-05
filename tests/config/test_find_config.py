import os
import tempfile
from pathlib import Path

from arachna.config import find_config


def test_finds_in_cwd():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text("{}")
        wd = os.getcwd()
        os.chdir(d)
        try:
            assert find_config() is not None
        finally:
            os.chdir(wd)


def test_finds_in_parent():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text("{}")
        sub = Path(d) / "a" / "b"
        sub.mkdir(parents=True)
        wd = os.getcwd()
        os.chdir(sub)
        try:
            assert find_config() is not None
        finally:
            os.chdir(wd)


def test_not_found():
    with tempfile.TemporaryDirectory() as d:
        wd = os.getcwd()
        os.chdir(d)
        try:
            assert find_config() is None
        finally:
            os.chdir(wd)
