import json

from arachna.config.config import get_profile, load_config


def test_fills_defaults(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"t": {"directories": ["src"]}}})
    )
    config = load_config(root=tmp_path)
    p = get_profile("t", root=tmp_path, config=config)
    assert p["split_mode"] == "by_file"
    assert p["max_tokens"] == 16000


def test_default_profile(tmp_path):
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    config = load_config(root=tmp_path)
    p = get_profile("default", root=tmp_path, config=config)
    assert p["max_tokens"] == 32000
