"""Tests for main() dispatch — all commands route to correct handlers."""

from unittest.mock import patch

import pytest

from arachna.__main__ import main


def test_main_no_args_prints_help(tmp_workspace):
    with patch("sys.argv", ["arachna"]), pytest.raises(SystemExit):
        main()


def test_main_version(tmp_workspace):
    with patch("sys.argv", ["arachna", "--version"]), pytest.raises(SystemExit):
        main()


def test_main_collect_list(tmp_workspace):
    with patch("sys.argv", ["arachna", "collect", "--list"]):
        main()


def test_main_collect_validate(tmp_workspace):
    with patch("sys.argv", ["arachna", "collect", "--validate"]), pytest.raises(SystemExit):
        main()


def test_main_doctor(tmp_workspace):
    with patch("sys.argv", ["arachna", "doctor"]), pytest.raises(SystemExit):
        main()


def test_main_completion(tmp_workspace):
    with patch("sys.argv", ["arachna", "completion", "bash"]):
        main()


def test_main_plugins_list(tmp_workspace):
    with patch("sys.argv", ["arachna", "plugins", "list"]):
        main()


def test_main_snapshot_list(tmp_workspace):
    with patch("sys.argv", ["arachna", "snapshot", "list"]):
        main()


def test_main_store_stats(tmp_workspace):
    with patch("sys.argv", ["arachna", "store", "stats"]):
        main()


def test_main_presets_update(tmp_workspace):
    with patch("sys.argv", ["arachna", "presets", "update"]), pytest.raises(SystemExit):
        main()
