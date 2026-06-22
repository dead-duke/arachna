"""Tests for shell command substitution blocking and CRLF sanitization."""

import json
from unittest.mock import patch

from arachna.domain.execution.runner import _check_shell_metachars, _validate_command, run_command
from tests.conftest import make_popen_mock

# -- $() and backticks blocked --


def test_dollar_paren_blocked_in_pre_commands_mode():
    """$() is blocked even when shell metacharacters are otherwise allowed."""
    is_safe, reason = _check_shell_metachars("echo $(whoami)", allow_file_args=True)
    assert not is_safe
    assert "command substitution" in reason


def test_backtick_blocked_in_pre_commands_mode():
    """Backticks are blocked even when shell metacharacters are otherwise allowed."""
    is_safe, reason = _check_shell_metachars("echo `whoami`", allow_file_args=True)
    assert not is_safe
    assert "command substitution" in reason


def test_dollar_paren_blocked_in_restricted_mode():
    """$() is blocked in restricted mode via shell metacharacters check."""
    is_safe, reason = _check_shell_metachars("echo $(whoami)", allow_file_args=False)
    assert not is_safe
    assert "shell metacharacters" in reason


def test_backtick_blocked_in_restricted_mode():
    """Backticks are blocked in restricted mode via shell metacharacters check."""
    is_safe, reason = _check_shell_metachars("echo `whoami`", allow_file_args=False)
    assert not is_safe
    assert "shell metacharacters" in reason


def test_validate_command_blocks_dollar_paren_in_pre_commands():
    """Full validation pipeline blocks $() with allow_file_args=True."""
    is_safe, reason = _validate_command("echo $(whoami)", allow_file_args=True)
    assert not is_safe
    assert "command substitution" in reason


def test_validate_command_blocks_backtick_in_pre_commands():
    """Full validation pipeline blocks backticks with allow_file_args=True."""
    is_safe, reason = _validate_command("echo `whoami`", allow_file_args=True)
    assert not is_safe
    assert "command substitution" in reason


def test_legitimate_pre_commands_pass_validation():
    """Real-world pre_commands like tree, git tag, git log still pass."""
    for cmd in [
        "tree -I '__pycache__|*.pyc' src",
        "git tag --sort=-creatordate",
        "git log --reverse --format='=== COMMIT: %h ==='",
    ]:
        is_safe, reason = _validate_command(cmd, allow_file_args=True)
        assert is_safe, f"Command '{cmd}' was blocked: {reason}"


# -- CRLF sanitized before logging --


def test_dangerous_override_sanitizes_newlines_before_logging():
    """Newlines in command are escaped before logger.error in dangerous override path."""
    from arachna.domain.execution.runner import _handle_dangerous_override

    with patch("arachna.domain.execution.runner.logger.error") as mock_log:
        _handle_dangerous_override(False, "blocked", True, "echo hello\nevil")
        logged_message = mock_log.call_args[0][1]
        assert "\n" not in logged_message
        assert "\\n" in logged_message


def test_dangerous_override_sanitizes_carriage_return_before_logging():
    """Carriage returns in command are escaped before logger.error."""
    from arachna.domain.execution.runner import _handle_dangerous_override

    with patch("arachna.domain.execution.runner.logger.error") as mock_log:
        _handle_dangerous_override(False, "blocked", True, "echo hello\revil")
        logged_message = mock_log.call_args[0][1]
        assert "\r" not in logged_message
        assert "\\r" in logged_message


def test_run_command_blocked_logs_sanitized_cmd(tmp_path):
    """Audit log for blocked command escapes newlines."""
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="output\n")
        run_command("echo hello\nevil", root=tmp_path)

    log_path = tmp_path / "out" / ".arachna_commands.log"
    content = log_path.read_text()
    assert "\\n" in content
    assert "\nevil" not in content
