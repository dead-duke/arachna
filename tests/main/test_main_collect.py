import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.__main__ import main


def test_collect_profile():
    with tempfile.TemporaryDirectory() as d:
        cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
        (Path(d) / ".arachna.json").write_text(json.dumps(cfg))
        (Path(d) / "src").mkdir()
        (Path(d) / "src" / "main.py").write_text("print('hi')")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--profile", "c"]):
                main()
        finally:
            os.chdir(wd)
        files = list((Path(d) / "arachna_context").glob("chat-c*.md"))
        assert len(files) == 1


def test_collect_all():
    with tempfile.TemporaryDirectory() as d:
        cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
        (Path(d) / ".arachna.json").write_text(json.dumps(cfg))
        (Path(d) / "src").mkdir()
        (Path(d) / "src" / "main.py").write_text("print('hi')")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--all"]):
                main()
        finally:
            os.chdir(wd)
        files = list((Path(d) / "arachna_context").glob("chat-c*.md"))
        assert len(files) == 1


def test_missing_profile():
    with tempfile.TemporaryDirectory() as d:
        cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}}
        (Path(d) / ".arachna.json").write_text(json.dumps(cfg))
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--profile", "x"]), patch("sys.exit") as ex:
                main()
                ex.assert_called_with(1)
        finally:
            os.chdir(wd)


def test_no_profiles_default():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text(json.dumps({"profiles": {}}))
        (Path(d) / "main.py").write_text("print('hi')")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--all"]):
                main()
        finally:
            os.chdir(wd)
        files = list((Path(d) / "arachna_context").glob("chat-default*.md"))
        assert len(files) == 1
