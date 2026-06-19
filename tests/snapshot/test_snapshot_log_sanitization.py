"""Tests for CRLF sanitization in snapshot command/pre_command warning logs."""

from unittest.mock import patch

from arachna.snapshot.snapshot_diff_commands import (
    _collect_snapshot_command,
    _collect_snapshot_pre_commands,
)


def test_pre_command_empty_output_sanitizes_newlines_in_log():
    """Newlines in pre_command are escaped before logger.warning."""
    profile = {"pre_commands": ["echo hello\nevil"]}

    with (
        patch("arachna.snapshot.snapshot_diff_commands.run_command", return_value=""),
        patch("arachna.snapshot.snapshot_diff_commands.logger.warning") as mock_log,
    ):
        _collect_snapshot_pre_commands(profile, root=None)
        logged_message = mock_log.call_args[0][1]
        assert "\n" not in logged_message
        assert "\\n" in logged_message


def test_pre_command_empty_output_sanitizes_carriage_return_in_log():
    """Carriage returns in pre_command are escaped before logger.warning."""
    profile = {"pre_commands": ["echo hello\revil"]}

    with (
        patch("arachna.snapshot.snapshot_diff_commands.run_command", return_value=""),
        patch("arachna.snapshot.snapshot_diff_commands.logger.warning") as mock_log,
    ):
        _collect_snapshot_pre_commands(profile, root=None)
        logged_message = mock_log.call_args[0][1]
        assert "\r" not in logged_message
        assert "\\r" in logged_message


def test_command_empty_output_sanitizes_newlines_in_log():
    """Newlines in command are escaped before logger.warning."""
    profile = {"command": "echo hello\nevil"}

    with (
        patch("arachna.snapshot.snapshot_diff_commands.run_command", return_value=""),
        patch("arachna.snapshot.snapshot_diff_commands.logger.warning") as mock_log,
    ):
        _collect_snapshot_command(profile, root=None)
        logged_message = mock_log.call_args[0][1]
        assert "\n" not in logged_message
        assert "\\n" in logged_message


def test_command_empty_output_sanitizes_carriage_return_in_log():
    """Carriage returns in command are escaped before logger.warning."""
    profile = {"command": "echo hello\revil"}

    with (
        patch("arachna.snapshot.snapshot_diff_commands.run_command", return_value=""),
        patch("arachna.snapshot.snapshot_diff_commands.logger.warning") as mock_log,
    ):
        _collect_snapshot_command(profile, root=None)
        logged_message = mock_log.call_args[0][1]
        assert "\r" not in logged_message
        assert "\\r" in logged_message


def test_pre_command_with_output_does_not_log_warning():
    """When pre_command produces output, no warning is logged."""
    profile = {"pre_commands": ["echo hello"]}

    with (
        patch("arachna.snapshot.snapshot_diff_commands.run_command", return_value="hello"),
        patch("arachna.snapshot.snapshot_diff_commands.write_object", return_value="abc123"),
        patch("arachna.snapshot.snapshot_diff_commands.logger.warning") as mock_log,
    ):
        _collect_snapshot_pre_commands(profile, root=None)
        mock_log.assert_not_called()
