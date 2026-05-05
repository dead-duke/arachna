"""Tests for runner — safe command execution."""

import subprocess
from unittest.mock import patch

from arachna.runner import run_command


def test_run_simple_command():
    result = run_command("echo hello")
    assert result.strip() == "hello"


def test_run_command_with_args():
    result = run_command("echo hello world")
    assert result.strip() == "hello world"


def test_run_nonexistent_command():
    result = run_command("nonexistent_command_xyz_123")
    assert result == ""


def test_run_command_timeout():
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="sleep", timeout=1)):
        result = run_command("sleep 10")
        assert result == ""


def test_run_command_os_error():
    with patch("subprocess.run", side_effect=OSError("wrong interpreter")):
        result = run_command("bad")
        assert result == ""


def test_run_with_shell_metacharacters():
    result = run_command("echo hello | cat")
    assert result.strip() == "hello"


def test_run_with_double_ampersand():
    result = run_command("echo first && echo second")
    lines = result.strip().split("\n")
    assert lines == ["first", "second"]
