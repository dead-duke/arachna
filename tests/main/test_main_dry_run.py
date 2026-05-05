import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.__main__ import main


def test_dry_run_profile():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text(
            json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
        )
        (Path(d) / "src").mkdir()
        (Path(d) / "src" / "main.py").write_text("print('hi')")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--profile", "c", "--dry-run"]):
                main()
        finally:
            os.chdir(wd)


def test_dry_run_all():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text(
            json.dumps({"profiles": {"a": {"command": "echo hi", "max_tokens": 100}}})
        )
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--all", "--dry-run"]):
                main()
        finally:
            os.chdir(wd)
