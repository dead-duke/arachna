"""Tests for config extends conflict warnings (v2.9.2)."""

import json

from arachna.config import get_profile, load_config


def test_config_extends_warns_on_conflict(tmp_path, capsys):
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
    get_profile("child", config=config)
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "max_tokens" in captured.out
    assert "overridden" in captured.out
