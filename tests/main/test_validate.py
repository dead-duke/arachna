import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.__main__ import main


def test_valid():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text(
            json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
        )
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--validate"]), patch("sys.exit") as ex:
                main()
                ex.assert_called_with(0)
        finally:
            os.chdir(wd)


def test_invalid():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text(json.dumps({"profiles": {"b": {"max_tokens": 0}}}))
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--validate"]), patch("sys.exit") as ex:
                main()
                ex.assert_called_with(1)
        finally:
            os.chdir(wd)
