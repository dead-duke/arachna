"""Tests for --diff --full CLI handler (v1.6.2)."""

import json
from pathlib import Path
from unittest.mock import patch

from arachna.__main__ import _cmd_diff, _cmd_diff_full, _combine_full_and_diff
from arachna.tokenizer import count_tokens


def test_combine_full_and_diff_basic(tmp_path, monkeypatch):
    """_combine_full_and_diff creates combined output with full context + diff."""
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"
    out.mkdir()

    full_parts = ["### src/main.py\n\n```python\nprint('hello')\n```\n"]
    diff_sections = [
        type(
            "MockSection",
            (),
            {"content": "### README.md\n\nADDED (new file):\n\n```\n# Project\n```\n"},
        )()
    ]

    created = _combine_full_and_diff(
        full_parts=full_parts,
        diff_sections=diff_sections,
        snapshot_id="test-snap",
        project_name="Test",
        title_tmpl="# Test (part {part})\n\n",
        max_tokens=32768,
        out_path=out,
        tokenizer=count_tokens,
    )

    assert len(created) == 1
    content = Path(created[0]).read_text()
    assert "FULL CONTEXT + DIFF" in content
    assert "main.py" in content
    assert "README.md" in content
    assert "test-snap" in content


def test_combine_full_and_diff_no_changes(tmp_path, monkeypatch):
    """_combine_full_and_diff with empty diff shows 'No changes' message."""
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"
    out.mkdir()

    full_parts = ["### src/main.py\n\n```python\ncode\n```\n"]

    created = _combine_full_and_diff(
        full_parts=full_parts,
        diff_sections=[],
        snapshot_id="snap1",
        project_name="Test",
        title_tmpl="# Test (part {part})\n\n",
        max_tokens=32768,
        out_path=out,
        tokenizer=count_tokens,
    )

    content = Path(created[0]).read_text()
    assert "No changes since snapshot" in content


def test_cmd_diff_full_success(tmp_path, monkeypatch):
    """_cmd_diff_full successfully creates combined output."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("original")
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 32768,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    from arachna.config import get_profile
    from arachna.watcher import create_snapshot

    profile = get_profile("code")
    create_snapshot(profile, name="full-test")

    (tmp_path / "src" / "main.py").write_text("modified")

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out

    config = json.loads((tmp_path / ".arachna.json").read_text())

    class DiffFullArgs:
        verbose = False
        compress = False
        format = "markdown"
        dry_run = False
        merge = False
        incremental = False
        all = False

    _cmd_diff_full(
        "full-test",
        "code",
        config,
        DiffFullArgs(),
        "test",
        out_dir,
    )
    sys.stdout = old

    files = list(out_dir.glob("chat-diff-full*"))
    assert len(files) >= 1
    content = files[0].read_text()
    assert "FULL CONTEXT + DIFF" in content


def test_cmd_diff_full_no_content(tmp_path, monkeypatch, capsys):
    """_cmd_diff_full prints message when no content collected."""
    monkeypatch.chdir(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "empty": {
                        "directories": ["nonexistent"],
                        "patterns": ["*.py"],
                        "max_tokens": 32768,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    from arachna.config import get_profile
    from arachna.watcher import create_snapshot

    profile = get_profile("empty")
    create_snapshot(profile, name="empty-snap")

    config = json.loads((tmp_path / ".arachna.json").read_text())

    class DiffFullArgs:
        verbose = False
        compress = False
        format = "markdown"
        dry_run = False
        merge = False
        incremental = False
        all = False

    _cmd_diff_full(
        "empty-snap",
        "empty",
        config,
        DiffFullArgs(),
        "test",
        out_dir,
    )

    captured = capsys.readouterr()
    assert "No content collected" in captured.out


def test_cmd_diff_dispatches_to_full(tmp_path, monkeypatch):
    """_cmd_diff with --full flag dispatches to _cmd_diff_full."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("hello")
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 32768,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    from arachna.config import get_profile
    from arachna.watcher import create_snapshot

    create_snapshot(get_profile("code"), name="diff-full-dispatch")

    with patch("arachna.__main__._cmd_diff_full") as mock_full:
        _cmd_diff(
            [
                "arachna",
                "--diff",
                "--from",
                "diff-full-dispatch",
                "--profile",
                "code",
                "--full",
            ]
        )
        mock_full.assert_called_once()
