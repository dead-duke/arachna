"""Tests for cli/init.py handlers — real behaviour, no mocks."""

import json
from argparse import Namespace

from arachna.cli.init import _dispatch_init
from arachna.config.profile_config import ArachnaConfig


def test_dispatch_init_with_hook_success(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    config = ArachnaConfig(project_name="test", output_dir="out", _root=str(tmp_path), profiles={})
    args = Namespace(defaults=False, preset=None, install_hook=True, output_dir=None, force=False)

    with __import__("contextlib").suppress(SystemExit):
        _dispatch_init(args, config)
    hook = tmp_path / ".git" / "hooks" / "post-commit"
    assert hook.exists()


def test_dispatch_init_with_hook_not_git(tmp_path):
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    config = ArachnaConfig(project_name="test", output_dir="out", _root=str(tmp_path), profiles={})
    args = Namespace(defaults=False, preset=None, install_hook=True, output_dir=None, force=False)
    import pytest

    with pytest.raises(SystemExit) as exc:
        _dispatch_init(args, config)
    assert exc.value.code == 1
