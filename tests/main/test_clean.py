import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.__main__ import main


def test_clean_numbered():
    with tempfile.TemporaryDirectory() as d:
        cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}}
        (Path(d) / ".arachna.json").write_text(json.dumps(cfg))
        ctx = Path(d) / "arachna_context"
        ctx.mkdir()
        (ctx / "chat-c_1.md").write_text("x")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--clean"]):
                main()
        finally:
            os.chdir(wd)
        assert not (ctx / "chat-c_1.md").exists()


def test_clean_plain():
    with tempfile.TemporaryDirectory() as d:
        cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}}
        (Path(d) / ".arachna.json").write_text(json.dumps(cfg))
        ctx = Path(d) / "arachna_context"
        ctx.mkdir()
        (ctx / "chat-c.md").write_text("x")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--clean"]):
                main()
        finally:
            os.chdir(wd)
        assert not (ctx / "chat-c.md").exists()


def test_clean_via_manifest():
    """Files tracked in manifest are cleaned even without matching pattern."""
    with tempfile.TemporaryDirectory() as d:
        cfg = {"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}}
        (Path(d) / ".arachna.json").write_text(json.dumps(cfg))
        ctx = Path(d) / "arachna_context"
        ctx.mkdir()
        # Create a file tracked by manifest
        mf = ctx / ".arachna_manifest.json"
        mf.write_text(json.dumps({"files": ["chat-x.md"]}))
        (ctx / "chat-x.md").write_text("data")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("sys.argv", ["arachna", "--clean"]):
                main()
        finally:
            os.chdir(wd)
        assert not (ctx / "chat-x.md").exists()
        assert not mf.exists()
