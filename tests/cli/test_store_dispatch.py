"""Dispatch edge case tests for store CLI handler."""

from argparse import ArgumentParser

import pytest

from arachna.cli.store import _dispatch_store


def test_dispatch_store_unknown_command_exits(tmp_path):
    """Unknown store command prints help and exits."""
    parser = ArgumentParser()
    store_sub = parser.add_subparsers(dest="command")
    store_sub.add_parser("store")

    config = {
        "project_name": "test",
        "output_dir": str(tmp_path / "out"),
        "_root": str(tmp_path),
        "profiles": {},
    }

    from argparse import Namespace

    args = Namespace(store_command="unknown_cmd")

    with pytest.raises(SystemExit):
        _dispatch_store(args, config, parser)
