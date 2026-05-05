import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.config import load_config


def test_no_file():
    with patch("arachna.config.find_config", return_value=None):
        c = load_config()
        assert c["project_name"] == "Project"


def test_from_file():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text(json.dumps({"project_name": "X"}))
        wd = os.getcwd()
        os.chdir(d)
        try:
            assert load_config()["project_name"] == "X"
        finally:
            os.chdir(wd)
