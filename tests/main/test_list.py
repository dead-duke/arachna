import json
from io import StringIO
from unittest.mock import patch

from arachna.__main__ import main


def test_list_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    out = StringIO()
    with patch("sys.argv", ["arachna", "collect", "--list"]), patch("sys.stdout", out):
        main()
    output = out.getvalue()
    assert "c:" in output
    assert "1 dirs" in output
    assert "100 tokens" in output


def test_list_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"profiles": {}}))
    out = StringIO()
    with patch("sys.argv", ["arachna", "collect", "--list"]), patch("sys.stdout", out):
        main()
    output = out.getvalue()
    assert "default" in output


def test_list_command_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"git": {"command": "echo hi", "max_tokens": 100}}})
    )
    out = StringIO()
    with patch("sys.argv", ["arachna", "collect", "--list"]), patch("sys.stdout", out):
        main()
    output = out.getvalue()
    assert "command" in output
