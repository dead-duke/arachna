"""Tests for interactive init — input handling, decline, overwrite, abort."""

import json
from unittest.mock import patch

from arachna.config.setup.init import run_interactive


def test_interactive_decline_all_profiles(tmp_path):
    """User declines all detected profiles — config created with empty profiles."""
    (tmp_path / "Dockerfile").write_text("FROM python")
    (tmp_path / ".git").mkdir()
    with (
        patch("arachna.config.setup.init.detect_presets", return_value=["docker", "git"]),
        patch("builtins.input", side_effect=["Test", "out", "16000", "n", "n", "y"]),
    ):
        run_interactive(tmp_path, output_dir=".")
    cfg = tmp_path / ".arachna.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert data["profiles"] == {}


def test_interactive_abort_on_existing(tmp_path):
    """User says no to overwrite — existing config preserved."""
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "keep-me"}))
    with patch("builtins.input", side_effect=["n"]):
        run_interactive(tmp_path, output_dir=".")
    data = json.loads((tmp_path / ".arachna.json").read_text())
    assert data["project_name"] == "keep-me"


def test_interactive_accepts_defaults_on_empty_input(tmp_path):
    """Empty inputs use defaults — project name from directory, output_dir='.', max_tokens=16000."""
    (tmp_path / "README.md").write_text("# Test")
    (tmp_path / ".git").mkdir()
    with (
        patch("arachna.config.setup.init.detect_presets", return_value=["docs", "git"]),
        patch("builtins.input", side_effect=["", "", "", "y", "y", "y"]),
    ):
        run_interactive(tmp_path, output_dir=".")
    cfg = tmp_path / ".arachna.json"
    data = json.loads(cfg.read_text())
    assert data["output_dir"] == "."
    assert "docs" in data["profiles"]


def test_interactive_command_profile_accepted(tmp_path):
    """Command-based profile (no dirs/files) — still offered and accepted."""
    (tmp_path / ".git").mkdir()
    with (
        patch("arachna.config.setup.init.detect_presets", return_value=["git"]),
        patch("builtins.input", side_effect=["Test", "out", "16000", "y", "y"]),
    ):
        run_interactive(tmp_path, output_dir=".")
    cfg = tmp_path / ".arachna.json"
    data = json.loads(cfg.read_text())
    assert "git" in data["profiles"]


def test_interactive_default_max_tokens_applied(tmp_path):
    """User's max_tokens applied to all accepted profiles."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    (tmp_path / ".git").mkdir()
    with (
        patch("arachna.config.setup.init.detect_presets", return_value=["python", "git"]),
        patch("builtins.input", side_effect=["Test", "out", "8000", "y", "y", "y"]),
    ):
        run_interactive(tmp_path, output_dir=".")
    cfg = tmp_path / ".arachna.json"
    data = json.loads(cfg.read_text())
    assert data["profiles"]["python"]["max_tokens"] == 8000
    assert data["profiles"]["git"]["max_tokens"] == 8000
