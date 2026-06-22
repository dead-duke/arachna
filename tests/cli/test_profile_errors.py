"""Tests for profile command — JSON output."""

import json
from io import StringIO

from arachna.cli.profile import _cmd_benchmark


def _make_args(profile="code", fmt="terminal", output_dir=None):
    from argparse import Namespace

    return Namespace(profile=profile, format=fmt, output_dir=output_dir)


def test_profile_json_output(tmp_path, make_config):
    """JSON format outputs valid JSON with all keys."""
    config = make_config(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def foo():\n    return 1\n")
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    _cmd_benchmark(_make_args(profile="code", fmt="json"), config)
    sys.stdout = old
    output = out.getvalue()
    lines = output.strip().split("\n", 1)
    assert len(lines) >= 2
    data = json.loads(lines[1])
    assert "full" in data
    assert "tokens" in data["full"]
