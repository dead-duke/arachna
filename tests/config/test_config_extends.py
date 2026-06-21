import json

import pytest

from arachna.config.config import get_profile, load_config


def test_config_extends_scalar(tmp_path):
    (tmp_path / "src").mkdir()
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
    config = load_config(root=tmp_path)
    profile = get_profile("child", root=tmp_path, config=config)
    assert profile.max_tokens == 32000
    assert profile.directories == ["src"]


def test_config_extends_exclude_append(tmp_path):
    (tmp_path / "src").mkdir()
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
    config = load_config(root=tmp_path)
    profile = get_profile("child", root=tmp_path, config=config)
    assert "*.pyc" in profile.exclude_patterns
    assert "*.log" in profile.exclude_patterns


def test_config_extends_source_override(tmp_path):
    (tmp_path / "lib").mkdir()
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
    config = load_config(root=tmp_path)
    profile = get_profile("child", root=tmp_path, config=config)
    assert profile.directories == ["lib"]


def test_config_extends_circular(tmp_path):
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
    config = load_config(root=tmp_path)
    with pytest.raises(ValueError, match="Circular"):
        get_profile("a", root=tmp_path, config=config)


def test_config_extends_deep_chain(tmp_path):
    (tmp_path / "src").mkdir()
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
    config = load_config(root=tmp_path)
    profile = get_profile("child", root=tmp_path, config=config)
    assert profile.max_tokens == 500
    assert profile.directories == ["src"]
    assert profile.patterns == ["*.py"]
    assert "*.pyc" in profile.exclude_patterns
    assert "*.log" in profile.exclude_patterns
