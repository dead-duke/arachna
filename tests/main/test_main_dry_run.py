import json
from unittest.mock import patch

from arachna.__main__ import main


def test_dry_run_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    with patch("sys.argv", ["arachna", "--profile", "c", "--dry-run"]):
        main()


def test_dry_run_all(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"a": {"command": "echo hi", "max_tokens": 100}}})
    )
    with patch("sys.argv", ["arachna", "--all", "--dry-run"]):
        main()
