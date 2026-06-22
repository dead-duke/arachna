"""Tests for dispatch wrappers in __main__.py — _dispatch_snapshot_wrapper, _dispatch_store_wrapper, etc."""

import json
from argparse import Namespace
from unittest.mock import patch

import pytest

from arachna.__main__ import (
    _dispatch_init_wrapper,
    _dispatch_plugins_wrapper,
    _dispatch_snapshot_wrapper,
    _dispatch_store_wrapper,
)


def test_dispatch_init_wrapper_install_hook(tmp_path):
    """_dispatch_init_wrapper with install_hook=True calls install_hook."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )
    from arachna.config.profile_config import ArachnaConfig

    config = ArachnaConfig(project_name="test", output_dir="out", _root=str(tmp_path), profiles={})
    args = Namespace(defaults=False, preset=None, install_hook=True, output_dir=None, force=False)
    with patch("sys.exit") as mock_exit:
        _dispatch_init_wrapper(args, config)
        mock_exit.assert_called_with(0)


def test_dispatch_init_wrapper_defaults(tmp_path):
    """_dispatch_init_wrapper without install_hook calls _cmd_init."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    (tmp_path / ".git").mkdir()
    from arachna.config.profile_config import ArachnaConfig

    config = ArachnaConfig(project_name="test", output_dir="out", _root=str(tmp_path), profiles={})
    args = Namespace(defaults=True, preset=None, install_hook=False, output_dir=None, force=False)
    _dispatch_init_wrapper(args, config)
    assert (tmp_path / ".arachna.json").exists()


def test_dispatch_snapshot_wrapper_list(tmp_path):
    """_dispatch_snapshot_wrapper with snap_command='list' lists snapshots."""
    from arachna.config.profile_config import ArachnaConfig

    config = ArachnaConfig(project_name="test", output_dir="out", _root=str(tmp_path), profiles={})
    parser = Namespace()
    args = Namespace(snap_command="list")
    _dispatch_snapshot_wrapper(args, config, parser)


def test_dispatch_store_wrapper_stats(tmp_path):
    """_dispatch_store_wrapper with store_command='stats' shows stats."""
    from arachna.config.profile_config import ArachnaConfig

    config = ArachnaConfig(project_name="test", output_dir="out", _root=str(tmp_path), profiles={})
    parser = Namespace()
    args = Namespace(store_command="stats")
    _dispatch_store_wrapper(args, config, parser)


def test_dispatch_plugins_wrapper_list(tmp_path):
    """_dispatch_plugins_wrapper with plugins_command='list' lists plugins."""
    from arachna.config.profile_config import ArachnaConfig

    config = ArachnaConfig(project_name="test", output_dir="out", _root=str(tmp_path), profiles={})
    parser = Namespace()
    args = Namespace(plugins_command="list")
    _dispatch_plugins_wrapper(args, config, parser)


def test_dispatch_plugins_wrapper_unknown(tmp_path):
    """_dispatch_plugins_wrapper with unknown command exits 1."""
    from arachna.config.profile_config import ArachnaConfig

    config = ArachnaConfig(project_name="test", output_dir="out", _root=str(tmp_path), profiles={})
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    plugins_p = sub.add_parser("plugins")
    plugins_subs = plugins_p.add_subparsers(dest="plugins_command")
    plugins_subs.add_parser("list")
    args = Namespace(plugins_command="unknown_cmd")
    with pytest.raises(SystemExit):
        _dispatch_plugins_wrapper(args, config, parser)
