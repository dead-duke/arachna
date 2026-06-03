"""Tests for --clean with chat-diff-full files (v1.6.2)."""

import json
from unittest.mock import patch

from arachna.__main__ import main


def test_clean_diff_full_files(tmp_path, monkeypatch):
    """_cmd_clean removes chat-diff-full files."""
    monkeypatch.chdir(tmp_path)
    cfg = {"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}}
    (tmp_path / ".arachna.json").write_text(json.dumps(cfg))
    ctx = tmp_path / "arachna_context"
    ctx.mkdir()
    (ctx / "chat-diff-full.md").write_text("combined output")
    (ctx / "chat-diff-full_1.md").write_text("combined part 1")
    (ctx / "chat-diff-full_2.md").write_text("combined part 2")

    with patch("sys.argv", ["arachna", "--clean"]):
        main()

    assert not (ctx / "chat-diff-full.md").exists()
    assert not (ctx / "chat-diff-full_1.md").exists()
    assert not (ctx / "chat-diff-full_2.md").exists()
