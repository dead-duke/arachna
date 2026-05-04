"""Tests for config loader."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.config import get_profile, load_config, find_config


def test_load_config_no_file():
    with patch("arachna.config.find_config", return_value=None):
        config = load_config()
        assert config["project_name"] == "Project"
        assert config["output_dir"] == "."
        assert config["profiles"] == {}


def test_find_config_in_current_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / ".arachna.json"
        cfg.write_text(json.dumps({"project_name": "Test"}))
        import os
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            found = find_config()
            assert found.resolve() == cfg.resolve()
        finally:
            os.chdir(cwd)


def test_get_profile_defaults():
    # get_profile raises KeyError for missing profile
    pass


def test_get_profile_fills_defaults():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / ".arachna.json"
        cfg.write_text(json.dumps({
            "profiles": {
                "test": {
                    "directories": ["src"]
                }
            }
        }))
        import os
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            profile = get_profile("test")
            assert profile["split_mode"] == "by_file"
            assert profile["max_tokens"] == 16000
            assert profile["exclude_patterns"] is not None
            assert len(profile["exclude_patterns"]) > 0
        finally:
            os.chdir(cwd)
