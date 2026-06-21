"""Shared fixtures for all tests."""

import json
from unittest.mock import MagicMock

import pytest

from arachna.config.profile_config import ArachnaConfig, ProfileConfig


def mock_popen(stdout=""):
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
                resolved[name] = _dict_to_profile_config(prof)
            else:
                resolved[name] = prof
        return ArachnaConfig(
            project_name="test",
            output_dir=str(output_dir or (tmp_path / "out")),
            profiles=resolved,
            _root=str(tmp_path),
        )

    return _make_config


def _dict_to_profile_config(d: dict) -> ProfileConfig:
    defaults = ProfileConfig()
    return ProfileConfig(
        name_template=d.get("name_template", defaults.name_template),
        title_template=d.get("title_template", defaults.title_template),
        max_tokens=d.get("max_tokens", defaults.max_tokens),
        split_mode=d.get("split_mode", defaults.split_mode),
        directories=d.get("directories", defaults.directories),
        patterns=d.get("patterns", defaults.patterns),
        files=d.get("files", defaults.files),
        exclude_patterns=d.get("exclude_patterns", defaults.exclude_patterns),
        pre_commands=d.get("pre_commands", defaults.pre_commands),
        post_commands=d.get("post_commands", defaults.post_commands),
        command=d.get("command"),
        section_format=d.get("section_format", defaults.section_format),
        compress=d.get("compress", defaults.compress),
        include_binary=d.get("include_binary", defaults.include_binary),
        binary_extensions=d.get("binary_extensions"),
        binary_max_mb=d.get("binary_max_mb", defaults.binary_max_mb),
        tokenizer=d.get("tokenizer", defaults.tokenizer),
        chars_per_token=d.get("chars_per_token"),
        line_numbers=d.get("line_numbers", defaults.line_numbers),
        extends=d.get("extends"),
        remote=d.get("remote", defaults.remote),
        use_gitignore=d.get("use_gitignore", defaults.use_gitignore),
        split_marker=d.get("split_marker", defaults.split_marker),
    )


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
def make_arachna_config():
    """Factory fixture for creating ArachnaConfig."""

    def _make_config(tmp_path, profiles=None, output_dir=None):
        profs = profiles or {}
        resolved = {}
        for name, prof in profs.items():
            if isinstance(prof, dict):
                resolved[name] = _dict_to_profile_config(prof)
            else:
                resolved[name] = prof
        return ArachnaConfig(
            project_name="test",
            output_dir=str(output_dir or (tmp_path / "out")),
            profiles=resolved,
        )

    return _make_config
