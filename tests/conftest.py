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


def make_profile(directory="src", patterns=None, files=None, **kw):
    """Shared profile factory for tests — single source of truth.

    Args:
        directory: Base directory for the profile (default: "src").
        patterns: Glob patterns for file matching (default: ["*"]).
        files: Explicit file paths (default: []).
        **kw: Overrides for any profile field.
    """
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
