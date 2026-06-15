"""TC-183: find_config accepts optional root parameter (v3.5.0)."""

import json

from arachna.config.config import find_config, load_config


def test_find_config_with_explicit_root(tmp_path):
    """find_config with explicit root finds config at that root."""
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "explicit-root", "profiles": {}})
    )
    cfg = find_config(root=tmp_path)
    assert cfg is not None
    assert cfg.parent == tmp_path


def test_find_config_not_found_with_root(tmp_path):
    """find_config with root that has no config returns None."""
    cfg = find_config(root=tmp_path)
    assert cfg is None


def test_load_config_with_root(tmp_path):
    """load_config with explicit root reads config from that root."""
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "loaded-root", "profiles": {}})
    )
    config = load_config(root=tmp_path)
    assert config["project_name"] == "loaded-root"
