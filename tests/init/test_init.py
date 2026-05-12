import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.init import run_defaults, run_interactive


def test_run_defaults_creates_config():
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hi')")
        (Path(d) / "README.md").write_text("# Project")
        wd = os.getcwd()
        os.chdir(d)
        try:
            run_defaults(output_dir="out")
            cfg = Path(d) / ".arachna.json"
            assert cfg.exists()
            data = json.loads(cfg.read_text())
            assert "code" in data["profiles"]
            assert "git" in data["profiles"]
            assert data["output_dir"] == "out"
        finally:
            os.chdir(wd)


def test_run_defaults_empty_project():
    with tempfile.TemporaryDirectory() as d:
        wd = os.getcwd()
        os.chdir(d)
        try:
            run_defaults(output_dir="out")
            cfg = Path(d) / ".arachna.json"
            assert cfg.exists()
            data = json.loads(cfg.read_text())
            assert "git" in data["profiles"]
            assert "code" not in data["profiles"]
        finally:
            os.chdir(wd)


def test_run_defaults_creates_output_dir():
    with tempfile.TemporaryDirectory() as d:
        wd = os.getcwd()
        os.chdir(d)
        try:
            run_defaults(output_dir="out")
            assert Path(d, "out").is_dir()
        finally:
            os.chdir(wd)


def test_run_defaults_detects_tests():
    with tempfile.TemporaryDirectory() as d:
        tests = Path(d) / "tests"
        tests.mkdir()
        (tests / "test_main.py").write_text("def test(): pass")
        wd = os.getcwd()
        os.chdir(d)
        try:
            run_defaults(output_dir="out")
            data = json.loads(Path(d, ".arachna.json").read_text())
            assert "tests" in data["profiles"]
        finally:
            os.chdir(wd)


def test_run_interactive_basic():
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hi')")
        (Path(d) / "README.md").write_text("# Project")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch(
                "builtins.input",
                side_effect=[
                    "TestProject",  # project name
                    "out",  # output dir
                    "16000",  # max tokens
                    "y",  # add code profile
                    "y",  # add tests? (no tests dir)
                    "y",  # add docs profile
                    "y",  # add git profile
                    "y",  # create config
                ],
            ):
                run_interactive(output_dir=".")
        finally:
            os.chdir(wd)
            cfg = Path(d) / ".arachna.json"
            if cfg.exists():
                data = json.loads(cfg.read_text())
                assert data["project_name"] == "TestProject"
                assert data["output_dir"] == "out"


def test_run_interactive_defaults_on_enter():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "README.md").write_text("# Project")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch(
                "builtins.input",
                side_effect=[
                    "",  # default project name
                    "",  # default output dir
                    "",  # default max tokens
                    "y",  # add docs
                    "y",  # add git
                    "y",  # create
                ],
            ):
                run_interactive(output_dir=".")
        finally:
            os.chdir(wd)
