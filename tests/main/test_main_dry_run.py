import json
from io import StringIO
from unittest.mock import patch

from arachna.__main__ import main


def test_dry_run_profile_no_files_created(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    ctx = tmp_path / "arachna_context"
    out = StringIO()
    with (
        patch("sys.argv", ["arachna", "collect", "--profile", "c", "--dry-run"]),
        patch("sys.stdout", out),
    ):
        main()
    output = out.getvalue()
    assert "main.py" in output
    assert not ctx.exists() or not list(ctx.glob("chat-c*.md"))


def test_dry_run_all_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"a": {"command": "echo hi", "max_tokens": 100}}})
    )
    out = StringIO()
    with patch("sys.argv", ["arachna", "collect", "--all", "--dry-run"]), patch("sys.stdout", out):
        main()
    output = out.getvalue()
    assert "[a] section" in output


def test_dry_run_empty_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"empty": {"directories": ["nonexistent"], "max_tokens": 100}}})
    )
    out = StringIO()
    with (
        patch("sys.argv", ["arachna", "collect", "--profile", "empty", "--dry-run"]),
        patch("sys.stdout", out),
    ):
        main()
    output = out.getvalue()
    assert "section" in output


def test_dry_run_single_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"profiles": {"c": {"directories": ["src"], "max_tokens": 100}}})
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    ctx = tmp_path / "arachna_context"
    out = StringIO()
    with (
        patch("sys.argv", ["arachna", "collect", "--profile", "c", "--dry-run"]),
        patch("sys.stdout", out),
    ):
        main()
    output = out.getvalue()
    assert "main.py" in output
    assert not ctx.exists() or not list(ctx.glob("chat-c*.md"))
