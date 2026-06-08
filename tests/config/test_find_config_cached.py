"""TC-183: find_config is cached via load_config @lru_cache."""

import json

from arachna.config import load_config


def test_load_config_cached(tmp_path, monkeypatch):
    """Second call to load_config uses cache — no additional disk reads."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "cached-test", "profiles": {}})
    )

    # First call — loads from disk
    cfg1 = load_config()
    assert cfg1["project_name"] == "cached-test"

    # Second call — uses cache (same object)
    cfg2 = load_config()
    assert cfg2 is cfg1  # Same object from cache

    # Clear cache for subsequent tests
    load_config.cache_clear()


def test_load_config_cache_isolated(tmp_path, monkeypatch):
    """Cache returns same config for same cwd."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "isolated", "profiles": {}})
    )

    cfg1 = load_config()
    cfg2 = load_config()
    assert cfg1["project_name"] == cfg2["project_name"]
    assert cfg1 is cfg2  # Same cached object

    load_config.cache_clear()
