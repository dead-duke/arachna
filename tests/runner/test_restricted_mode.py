"""Tests for restricted mode in run_command (v2.9.0)."""

import subprocess
from unittest.mock import patch

from arachna.runner import _validate_command, run_command


def _completed_process(stdout="", stderr="", returncode=0, args=None):
    return subprocess.CompletedProcess(
        args=args or ["echo", "hello"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_restricted_mode_allows_safe_commands():
    """Restricted mode allows echo, pwd, date, etc."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="hello\n")
        result = run_command("echo hello")
        assert result == "hello\n"


def test_restricted_mode_blocks_cat():
    """Restricted mode blocks cat (needs allow_file_args)."""
    is_safe, reason = _validate_command("cat file.txt")
    assert not is_safe
    assert "not in allowlist" in reason


def test_restricted_mode_blocks_shell_metachar():
    """Restricted mode blocks shell metacharacters."""
    is_safe, reason = _validate_command("echo hello | cat")
    assert not is_safe
    assert "shell metacharacters" in reason


def test_pre_commands_mode_allows_cat():
    """Pre_commands mode (allow_file_args=True) allows cat, grep, etc."""
    is_safe, reason = _validate_command("cat file.txt", allow_file_args=True)
    assert is_safe


def test_pre_commands_mode_allows_pipe():
    """Pre_commands mode allows pipes."""
    is_safe, reason = _validate_command("echo hello | cat", allow_file_args=True)
    assert is_safe


def test_restricted_mode_blocks_shell_redirect():
    """Restricted mode blocks > redirection."""
    is_safe, reason = _validate_command("echo hello > /tmp/out")
    assert not is_safe


def test_run_command_restricted_blocks_cat():
    """run_command without allow_file_args blocks cat."""
    result = run_command("cat /etc/passwd")
    assert result == ""


def test_run_command_pre_commands_allows_cat():
    """run_command with allow_file_args allows cat."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="content\n")
        result = run_command("cat file.txt", allow_file_args=True)
        assert result == "content\n"
