"""Shared fixtures for all tests."""

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


def make_profile(**kw):
    """Shared profile factory for tests — single source of truth."""
    return {
        "name_template": "c",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
        **kw,
    }
