"""TC-183: find_config is cached via @lru_cache."""

import json

from arachna.config import find_config, load_config


def test_find_config_cached(tmp_path, monkeypatch):
    """Second call to find_config uses cache — same result, no disk I/O."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "cached-test", "profiles": {}})
    )

    cfg1 = find_config()
    cfg2 = find_config()
    assert cfg1 is not None
    assert cfg2 is cfg1


def test_load_config_reads_file(tmp_path, monkeypatch):
    """load_config reads .arachna.json each time (not cached)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "isolated", "profiles": {}})
    )

    cfg1 = load_config()
    cfg2 = load_config()
    assert cfg1["project_name"] == cfg2["project_name"]
