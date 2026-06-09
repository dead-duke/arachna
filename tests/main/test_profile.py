"""Tests for profile command."""

import json
from io import StringIO

from arachna.__main__ import _cmd_benchmark


def _make_args(profile="code", fmt="terminal", output_dir=None):
    from argparse import Namespace

    return Namespace(profile=profile, format=fmt, output_dir=output_dir)


def test_profile_terminal_output(tmp_path, monkeypatch):
    """Profile prints table with all modes."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    import sys

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_benchmark(_make_args(profile="code"), json.loads((tmp_path / ".arachna.json").read_text()))
    sys.stdout = old

    output = out.getvalue()
    assert "full" in output
    assert "repo-map" in output
    assert "incremental" in output
    assert "Summary" in output


def test_profile_json_output(tmp_path, monkeypatch):
    """Profile --format json outputs machine-readable JSON after the status line."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": "out",
                "profiles": {
                    "code": {
                        "directories": ["src"],
                        "patterns": ["*.py"],
                        "max_tokens": 16000,
                        "split_mode": "by_file",
                        "use_gitignore": False,
                    }
                },
            }
        )
    )

    import sys

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_benchmark(
        _make_args(profile="code", fmt="json"),
        json.loads((tmp_path / ".arachna.json").read_text()),
    )
    sys.stdout = old

    output = out.getvalue()
    lines = output.strip().split("\n", 1)
    assert len(lines) >= 2
    data = json.loads(lines[1])
    assert "full" in data
    assert "tokens" in data["full"]
    assert "time" in data["full"]
