"""Tests for config extends conflict warnings (v2.9.2)."""

import json

from arachna.config import get_profile


def test_config_extends_warns_on_conflict(tmp_path, monkeypatch, capsys):
    """Warning printed when child overrides parent scalar."""
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
    get_profile("child")
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "max_tokens" in captured.out
    assert "overridden" in captured.out
