import json
from unittest.mock import patch

from arachna.__main__ import main


def test_clean_numbered(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    ctx = tmp_path / "arachna_context"
    ctx.mkdir()
    (ctx / "chat-c_1.md").write_text("x")
    with patch("sys.argv", ["arachna", "--clean"]):
        main()
    assert not (ctx / "chat-c_1.md").exists()


def test_clean_plain(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    ctx = tmp_path / "arachna_context"
    ctx.mkdir()
    (ctx / "chat-c.md").write_text("x")
    with patch("sys.argv", ["arachna", "--clean"]):
        main()
    assert not (ctx / "chat-c.md").exists()


def test_clean_via_manifest(tmp_path, monkeypatch):
    """Files tracked in manifest are cleaned even without matching pattern."""
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"x": {"command": "echo hi", "max_tokens": 100}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    ctx = tmp_path / "arachna_context"
    ctx.mkdir()
    # Create a file tracked by manifest
    mf = ctx / ".arachna_manifest.json"
    mf.write_text(json.dumps({"files": ["chat-x.md"]}))
    (ctx / "chat-x.md").write_text("data")
    with patch("sys.argv", ["arachna", "--clean"]):
        main()
    assert not (ctx / "chat-x.md").exists()
    assert not mf.exists()
