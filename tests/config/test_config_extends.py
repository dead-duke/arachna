"""Tests for config inheritance via 'extends' field (v2.9.2)."""

import json

import pytest

from arachna.config import get_profile


def test_config_extends_scalar(tmp_path, monkeypatch):
    """Child scalar overrides parent."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "profiles": {
                    "base": {"directories": ["src"], "max_tokens": 16000, "split_mode": "by_file"},
                    "child": {"extends": "base", "max_tokens": 32000},
                },
            }
        )
    )
    profile = get_profile("child")
    assert profile["max_tokens"] == 32000
    assert profile["directories"] == ["src"]


def test_config_extends_exclude_append(tmp_path, monkeypatch):
    """Exclusion lists concatenate."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "profiles": {
                    "base": {
                        "directories": ["src"],
                        "max_tokens": 100,
                        "exclude_patterns": ["*.pyc"],
                    },
                    "child": {"extends": "base", "exclude_patterns": ["*.log"]},
                },
            }
        )
    )
    profile = get_profile("child")
    assert "*.pyc" in profile["exclude_patterns"]
    assert "*.log" in profile["exclude_patterns"]


def test_config_extends_source_override(tmp_path, monkeypatch):
    """Child directories replaces parent."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "profiles": {
                    "base": {"directories": ["src"], "max_tokens": 100},
                    "child": {"extends": "base", "directories": ["lib"]},
                },
            }
        )
    )
    (tmp_path / "lib").mkdir()
    profile = get_profile("child")
    assert profile["directories"] == ["lib"]


def test_config_extends_circular(tmp_path, monkeypatch):
    """Circular extends raises ValueError."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "profiles": {
                    "a": {"extends": "b", "directories": ["src"], "max_tokens": 100},
                    "b": {"extends": "a", "directories": ["src"], "max_tokens": 100},
                },
            }
        )
    )
    with pytest.raises(ValueError, match="Circular"):
        get_profile("a")


def test_config_extends_deep_chain(tmp_path, monkeypatch):
    """Chain of 3 profiles merges correctly."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "profiles": {
                    "base": {
                        "directories": ["src"],
                        "max_tokens": 100,
                        "exclude_patterns": ["*.pyc"],
                    },
                    "mid": {"extends": "base", "patterns": ["*.py"], "exclude_patterns": ["*.log"]},
                    "child": {"extends": "mid", "max_tokens": 500},
                },
            }
        )
    )
    profile = get_profile("child")
    assert profile["max_tokens"] == 500
    assert profile["directories"] == ["src"]
    assert profile["patterns"] == ["*.py"]
    assert "*.pyc" in profile["exclude_patterns"]
    assert "*.log" in profile["exclude_patterns"]
