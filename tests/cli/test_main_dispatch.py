"""Tests for main() dispatch in __main__.py."""

from unittest.mock import patch

import pytest

from arachna.__main__ import main


def test_main_no_args_prints_help():
    with patch("sys.argv", ["arachna"]), pytest.raises(SystemExit):
        main()


def test_main_version():
    with patch("sys.argv", ["arachna", "--version"]), pytest.raises(SystemExit):
        main()


def test_main_collect_list():
    with patch("sys.argv", ["arachna", "collect", "--list"]):
        main()


def test_main_collect_validate():
    with patch("sys.argv", ["arachna", "collect", "--validate"]), pytest.raises(SystemExit):
        main()


def test_main_doctor():
    with patch("sys.argv", ["arachna", "doctor"]), pytest.raises(SystemExit):
        main()


def test_main_completion():
    with patch("sys.argv", ["arachna", "completion", "bash"]):
        main()


def test_main_plugins_list():
    with patch("sys.argv", ["arachna", "plugins", "list"]):
        main()


def test_main_snapshot_list():
    with patch("sys.argv", ["arachna", "snapshot", "list"]):
        main()


def test_main_store_stats():
    with patch("sys.argv", ["arachna", "store", "stats"]):
        main()


def test_main_presets_update():
    with patch("sys.argv", ["arachna", "presets", "update"]), pytest.raises(SystemExit):
        main()
