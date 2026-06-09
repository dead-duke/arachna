import json
from unittest.mock import patch

from arachna.__main__ import main


def test_compress_cli(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")
    with patch("sys.argv", ["arachna", "collect", "--profile", "c", "--compress"]):
        main()
    files = list((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "\n\n\n\n" not in content


def test_compress_cli_no_flag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")
    with patch("sys.argv", ["arachna", "collect", "--profile", "c"]):
        main()
    files = list((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert content.count("\n\n\n\n") >= 1
