import json

from arachna.config.core.config import get_profile, load_config


def test_config_extends_overrides_silently(tmp_path):
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
