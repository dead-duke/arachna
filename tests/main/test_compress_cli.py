import json
from unittest.mock import patch

from arachna.__main__ import main


def test_compress_cli(tmp_path, monkeypatch):
    """--compress reduces output by collapsing blank lines."""
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    # File with extra blank lines
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")
    with patch("sys.argv", ["arachna", "--profile", "c", "--compress"]):
        main()
    files = list((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    # Blank lines collapsed: 3+ -> 2
    assert "\n\n\n\n" not in content


def test_compress_cli_no_flag(tmp_path, monkeypatch):
    """Without --compress, blank lines are preserved."""
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("a\n\n\n\nb\n")
    with patch("sys.argv", ["arachna", "--profile", "c"]):
        main()
    files = list((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    # Four blank lines preserved
    assert content.count("\n\n\n\n") >= 1
