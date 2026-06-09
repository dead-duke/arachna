import json
from unittest.mock import patch

from arachna.__main__ import main


def test_collect_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    with patch("sys.argv", ["arachna", "collect", "--profile", "c"]):
        main()
    files = list((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files) == 1


def test_collect_all(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    with patch("sys.argv", ["arachna", "collect", "--all"]):
        main()
    files = list((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files) == 1


def test_no_profiles_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    (tmp_path / "main.py").write_text("print('hi')")
    with patch("sys.argv", ["arachna", "collect", "--all"]):
        main()
    files = list((tmp_path / "arachna_context").glob("chat-default*.md"))
    assert len(files) == 1
