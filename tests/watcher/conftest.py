"""Shared fixtures for watcher tests."""

import json

import pytest


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


@pytest.fixture
def setup_config(tmp_path, monkeypatch):
    """Create minimal .arachna.json and chdir to tmp_path."""

    def _setup(profiles=None):
        monkeypatch.chdir(tmp_path)
        config = {"project_name": "test", "output_dir": "out", "profiles": profiles or {}}
        (tmp_path / ".arachna.json").write_text(json.dumps(config))

    return _setup
