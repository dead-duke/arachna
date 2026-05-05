import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.__main__ import main


def test_list():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text(
            json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
        )
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--list"]):
                main()
        finally:
            os.chdir(wd)
