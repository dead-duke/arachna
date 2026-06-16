"""Shared fixtures for API tests."""

import json

import pytest


@pytest.fixture
def setup_config(tmp_path):
    """Create minimal .arachna.json in tmp_path."""

    def _setup(profiles=None):
        config = {"project_name": "test", "output_dir": "out", "profiles": profiles or {}}
        (tmp_path / ".arachna.json").write_text(json.dumps(config))
        return tmp_path

    return _setup


@pytest.fixture
def make_profile():
    """Factory fixture for creating profile dicts."""

    def _make_profile(directory, patterns=None, files=None):
        return {
            "directories": [directory],
            "patterns": patterns or ["*"],
            "files": files or [],
            "exclude_patterns": [],
            "use_gitignore": False,
        }

    return _make_profile
