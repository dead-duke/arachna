import json
from io import StringIO

from arachna.cli.collect import _cmd_collect_list
from arachna.config.core.config import load_config


def _args():
    from argparse import Namespace

    return Namespace()


def test_list_output(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": str(tmp_path / "out"),
                "profiles": {"c": {"directories": ["src"], "max_tokens": 100}},
            }
        )
    )
    config = load_config(root=tmp_path)
    config._root = str(tmp_path)
    import sys

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_collect_list(_args(), config)
    sys.stdout = old
    output = out.getvalue()
    assert "c:" in output
    assert "1 dirs" in output
    assert "100 tokens" in output


def test_list_empty(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": str(tmp_path / "out"),
                "profiles": {},
            }
        )
    )
    config = load_config(root=tmp_path)
    config._root = str(tmp_path)
    import sys

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_collect_list(_args(), config)
    sys.stdout = old
    output = out.getvalue()
    assert "default" in output


def test_list_command_profile(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": str(tmp_path / "out"),
                "profiles": {"git": {"command": "echo hi", "max_tokens": 100}},
            }
        )
    )
    config = load_config(root=tmp_path)
    config._root = str(tmp_path)
    import sys

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_collect_list(_args(), config)
    sys.stdout = old
    output = out.getvalue()
    assert "command" in output
