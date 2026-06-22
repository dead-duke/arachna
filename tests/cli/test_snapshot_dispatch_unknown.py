"""Tests for snapshot dispatch — unknown subcommand exits with error."""

from argparse import ArgumentParser

import pytest

from arachna.cli.snapshot import _dispatch_snapshot
from arachna.config.profile_config import ArachnaConfig


def test_dispatch_snapshot_unknown_command(tmp_path):
    """Unknown snapshot subcommand prints help and exits."""
    parser = ArgumentParser()
    snap_sub = parser.add_subparsers(dest="command")
    snap_sub.add_parser("snapshot")

    config = ArachnaConfig(project_name="test", output_dir="out", _root=str(tmp_path), profiles={})
    from argparse import Namespace

    args = Namespace(snap_command="unknown_cmd")

    with pytest.raises(SystemExit):
        _dispatch_snapshot(args, config, parser)
