"""Tests for build_argparse in __main__.py."""

import pytest

from arachna.__main__ import build_argparse


def test_argparse_has_version():
    parser = build_argparse()
    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])


def test_argparse_collect_subparser():
    parser = build_argparse()
    args = parser.parse_args(["collect", "--list"])
    assert args.command == "collect"


def test_argparse_snapshot_subparser():
    parser = build_argparse()
    args = parser.parse_args(["snapshot", "list"])
    assert args.command == "snapshot"
    assert args.snap_command == "list"


def test_argparse_diff_subparser():
    parser = build_argparse()
    args = parser.parse_args(["diff", "--all"])
    assert args.command == "diff"


def test_argparse_store_subparser():
    parser = build_argparse()
    args = parser.parse_args(["store", "stats"])
    assert args.command == "store"


def test_argparse_plugins_subparser():
    parser = build_argparse()
    args = parser.parse_args(["plugins", "list"])
    assert args.command == "plugins"


def test_argparse_presets_subparser():
    parser = build_argparse()
    args = parser.parse_args(["presets", "update"])
    assert args.command == "presets"


def test_argparse_doctor_subparser():
    parser = build_argparse()
    args = parser.parse_args(["doctor"])
    assert args.command == "doctor"


def test_argparse_init_subparser():
    parser = build_argparse()
    args = parser.parse_args(["init", "--defaults"])
    assert args.command == "init"


def test_argparse_completion_subparser():
    parser = build_argparse()
    args = parser.parse_args(["completion", "bash"])
    assert args.command == "completion"


def test_argparse_profile_subparser():
    parser = build_argparse()
    args = parser.parse_args(["profile", "--profile", "code"])
    assert args.command == "profile"


def test_argparse_collect_with_all_flags():
    parser = build_argparse()
    args = parser.parse_args(
        [
            "collect",
            "--profile",
            "code",
            "--compress",
            "--format",
            "json",
            "--output-dir",
            "/tmp",
            "--verbose",
            "--incremental",
            "--merge",
            "--query",
            "auth",
            "--mode",
            "headers",
            "--no-pre-commands",
        ]
    )
    assert args.profile == "code"
    assert args.compress
    assert args.format == "json"
    assert args.output_dir == "/tmp"
    assert args.verbose
    assert args.incremental
    assert args.merge
    assert args.query == "auth"
    assert args.mode == "headers"
    assert args.no_pre_commands


def test_argparse_diff_with_all_flags():
    parser = build_argparse()
    args = parser.parse_args(
        [
            "diff",
            "--from",
            "snap1",
            "--to",
            "snap2",
            "--profile",
            "code",
            "--format",
            "xml",
            "--mode",
            "structural",
            "--compress",
            "--output-dir",
            "/tmp",
            "--query",
            "auth",
            "--flat",
            "--stat",
        ]
    )
    assert args.from_snapshot == "snap1"
    assert args.to == "snap2"
    assert args.format == "xml"
    assert args.mode == "structural"
    assert args.compress
    assert args.flat
    assert args.stat


def test_argparse_snapshot_create():
    parser = build_argparse()
    args = parser.parse_args(["snapshot", "create", "--name", "test", "--profile", "code"])
    assert args.snap_command == "create"
    assert args.name == "test"
    assert args.profile == "code"


def test_argparse_snapshot_info():
    parser = build_argparse()
    args = parser.parse_args(["snapshot", "info", "my-snap", "--profile", "--stats"])
    assert args.snap_command == "info"
    assert args.id == "my-snap"
    assert args.profile_only
    assert args.stats_only
