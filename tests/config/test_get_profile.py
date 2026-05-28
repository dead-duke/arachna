import json

from arachna.config import get_profile


def test_fills_defaults(tmp_path, monkeypatch):
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {"t": {"directories": ["x"]}}}))
    monkeypatch.chdir(tmp_path)
    p = get_profile("t")
    assert p["split_mode"] == "by_file"
    assert p["max_tokens"] == 16000


def test_default_profile(tmp_path, monkeypatch):
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    monkeypatch.chdir(tmp_path)
    p = get_profile("default")
    assert p["max_tokens"] == 32000
