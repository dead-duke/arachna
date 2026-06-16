"""Shared fixtures for all tests."""

import json

import pytest


@pytest.fixture
def make_config():
    """Factory fixture for creating config dicts with _root."""

    def _make_config(tmp_path, profiles=None, dirs=None, output_dir=None):
        return {
            "project_name": "test",
            "output_dir": str(output_dir or (tmp_path / "out")),
            "_root": str(tmp_path),
            "profiles": profiles
            or {
                "code": {
                    "directories": dirs or ["src"],
                    "patterns": ["*.py"],
                    "max_tokens": 16000,
                    "split_mode": "by_file",
                    "use_gitignore": False,
                }
            },
        }

    return _make_config


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
    """Factory fixture for creating profile dicts — single source of truth.

    Returns a callable that creates profile dicts.
    Usage: profile = make_profile("src", ["*.py"])
    """

    def _make_profile(directory="src", patterns=None, files=None, **kw):
        return {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": [directory],
            "patterns": patterns or ["*"],
            "files": files or [],
            "exclude_patterns": [],
            "use_gitignore": False,
            **kw,
        }

    return _make_profile
