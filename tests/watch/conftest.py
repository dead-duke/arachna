"""Shared fixtures for watcher tests."""

import json

import pytest


@pytest.fixture
def setup_config(tmp_path):
    """Create minimal .arachna.json in tmp_path. No chdir."""

    def _setup(profiles=None):
        config = {"project_name": "test", "output_dir": "out", "profiles": profiles or {}}
        (tmp_path / ".arachna.json").write_text(json.dumps(config))
        return tmp_path

    return _setup


@pytest.fixture
def make_profile():
    """Factory fixture for creating profile dicts — delegates to tests.conftest.make_profile."""
    from tests.conftest import make_profile as _make_profile

    def _factory(directory, patterns=None, files=None):
        return _make_profile(directory=directory, patterns=patterns, files=files)

    return _factory
