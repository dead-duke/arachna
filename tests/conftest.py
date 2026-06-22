"""Shared fixtures for all tests."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arachna.config.profile_config import ArachnaConfig, ProfileConfig


def make_popen_mock(stdout=""):
    """Create a mock subprocess.Popen that returns given stdout."""
    mock = MagicMock()
    mock.stdout.read.side_effect = [stdout, ""]
    mock.wait.return_value = 0
    return mock


@pytest.fixture
def make_config():
    """Factory fixture for creating ArachnaConfig with _root."""

    def _make_config(tmp_path, profiles=None, dirs=None, output_dir=None):
        prof_cfg = ProfileConfig(
            name_template="chat-code",
            title_template="# T (part {part})\n\n",
            max_tokens=16000,
            split_mode="by_file",
            directories=dirs or ["src"],
            patterns=["*.py"],
            use_gitignore=False,
        )
        profs = profiles or {"code": prof_cfg}
        resolved = {}
        for name, prof in profs.items():
            if isinstance(prof, dict):
                resolved[name] = ProfileConfig.from_dict(prof)
            else:
                resolved[name] = prof
        return ArachnaConfig(
            project_name="test",
            output_dir=str(output_dir or (tmp_path / "out")),
            profiles=resolved,
            _root=str(tmp_path),
        )

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
    """Factory fixture for creating ProfileConfig."""

    def _make_profile(directory="src", patterns=None, files=None, **kw):
        return ProfileConfig(
            name_template="c",
            title_template="# T (part {part})\n\n",
            max_tokens=16000,
            split_mode="by_file",
            directories=[directory],
            patterns=patterns or ["*"],
            files=files or [],
            exclude_patterns=[],
            use_gitignore=False,
            **kw,
        )

    return _make_profile


@pytest.fixture
def tmp_workspace(tmp_path):
    """Create isolated workspace with .arachna.json and patch cwd to tmp_path."""
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    (tmp_path / "out").mkdir()
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield tmp_path
