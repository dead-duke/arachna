"""Tests for _validate_command allow_dangerous branches."""

from arachna.domain.runner import _validate_command


def test_allow_dangerous_pipe_unknown():
    """allow_dangerous=True allows unknown commands in pipe."""
    is_safe, reason = _validate_command(
        "echo hello | python3 -c 'print(1)'", allow_dangerous=True, allow_file_args=True
    )
    assert is_safe


def test_allow_dangerous_shell_metachar():
    """allow_dangerous=True allows shell metacharacters."""
    is_safe, reason = _validate_command(
        "echo hello > /tmp/x", allow_dangerous=True, allow_file_args=True
    )
    assert is_safe


def test_allow_dangerous_unknown_command():
    """allow_dangerous=True allows unknown commands."""
    is_safe, reason = _validate_command("unknown_cmd_xyz", allow_dangerous=True)
    assert is_safe
