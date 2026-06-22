import json
from unittest.mock import patch

from arachna.cli.collect import _cmd_collect_validate
from arachna.config.core.config import load_config


def _args():
    from argparse import Namespace

    return Namespace()


def test_valid(tmp_path):
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
    with patch("sys.exit") as ex:
        _cmd_collect_validate(_args(), config)
        ex.assert_called_with(0)


def test_invalid(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "output_dir": str(tmp_path / "out"),
                "profiles": {"b": {"max_tokens": 0}},
            }
        )
    )
    config = load_config(root=tmp_path)
    config._root = str(tmp_path)
    with patch("sys.exit") as ex:
        _cmd_collect_validate(_args(), config)
        ex.assert_called_with(1)
