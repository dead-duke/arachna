"""Tests for restricted mode in run_command (v2.9.0)."""

from unittest.mock import patch

from arachna.domain.runner import _validate_command, run_command
from tests.domain.conftest import mock_popen


def test_restricted_mode_allows_safe_commands(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = mock_popen(stdout="hello\n")
        result = run_command("echo hello", root=tmp_path)
        assert result == "hello\n"


def test_restricted_mode_blocks_cat():
    is_safe, reason = _validate_command("cat file.txt")
    assert not is_safe
    assert "not in allowlist" in reason


def test_restricted_mode_blocks_shell_metachar():
    is_safe, reason = _validate_command("echo hello | cat")
    assert not is_safe
    assert "shell metacharacters" in reason


def test_pre_commands_mode_allows_cat():
    is_safe, reason = _validate_command("cat file.txt", allow_file_args=True)
    assert is_safe


def test_pre_commands_mode_allows_pipe():
    is_safe, reason = _validate_command("echo hello | cat", allow_file_args=True)
    assert is_safe


def test_restricted_mode_blocks_shell_redirect():
    is_safe, reason = _validate_command("echo hello > /tmp/out")
    assert not is_safe


def test_run_command_restricted_blocks_cat(tmp_path):
    result = run_command("cat /etc/passwd", root=tmp_path)
    assert result == ""


def test_run_command_pre_commands_allows_cat(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = mock_popen(stdout="content\n")
        result = run_command("cat file.txt", root=tmp_path, allow_file_args=True)
        assert result == "content\n"
