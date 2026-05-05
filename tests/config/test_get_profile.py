import json
import os
import tempfile
from pathlib import Path

from arachna.config import get_profile


def test_fills_defaults():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text(
            json.dumps({"profiles": {"t": {"directories": ["x"]}}})
        )
        wd = os.getcwd()
        os.chdir(d)
        try:
            p = get_profile("t")
            assert p["split_mode"] == "by_file"
            assert p["max_tokens"] == 16000
        finally:
            os.chdir(wd)


def test_default_profile():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".arachna.json").write_text(json.dumps({"profiles": {}}))
        wd = os.getcwd()
        os.chdir(d)
        try:
            p = get_profile("default")
            assert p["max_tokens"] == 32000
        finally:
            os.chdir(wd)
