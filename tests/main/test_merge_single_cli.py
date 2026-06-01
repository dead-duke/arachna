"""Tests for --profile X --merge CLI path (_cmd_single)."""

import json
from unittest.mock import patch

from arachna.__main__ import main


def test_merge_single_profile_cli(tmp_path, monkeypatch):
    """--profile X --merge appends to existing output."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 16000}}})
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print('hi')")
    with patch("sys.argv", ["arachna", "--profile", "c", "--merge"]):
        main()
    files1 = sorted((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files1) == 1
    assert "chat-c_1.md" in str(files1[0])

    # Second merge run
    with patch("sys.argv", ["arachna", "--profile", "c", "--merge"]):
        main()
    files2 = sorted((tmp_path / "arachna_context").glob("chat-c*.md"))
    assert len(files2) == 2
    assert "chat-c_2.md" in str(files2[1])
