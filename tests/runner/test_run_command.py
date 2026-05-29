import subprocess
from unittest.mock import MagicMock, patch

from arachna.runner import (
    _is_safe_command,
    _resolve_base,
    _validate_command,
    run_command,
)


def test_simple():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="hello\n", returncode=0)
        assert run_command("echo hello").strip() == "hello"


def test_with_args():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="hello world\n", returncode=0)
        assert run_command("echo hello world").strip() == "hello world"


def test_nonexistent():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert run_command("nonexistent_cmd_xyz") == ""


def test_timeout():
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="sleep", timeout=1)):
        assert run_command("sleep 10") == ""


def test_os_error():
    with patch("subprocess.run", side_effect=OSError("wrong interpreter")):
        assert run_command("bad") == ""


def test_pipe():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="hello\n", returncode=0)
        assert run_command("echo hello | cat").strip() == "hello"


def test_double_ampersand():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="first\nsecond\n", returncode=0)
        lines = run_command("echo first && echo second").strip().split("\n")
        assert lines == ["first", "second"]


def test_dry_run_safe_command():
    """Safe commands execute even in dry-run mode."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="hello\n", returncode=0)
        assert run_command("echo hello", dry_run=True).strip() == "hello"


def test_dry_run_unsafe_command():
    """Unsafe commands return empty in dry-run (non-interactive)."""
    result = run_command("python3 -c 'print(1)'", dry_run=True)
    # python3 not in allowlist, non-interactive → blocked by _validate_command
    assert result == ""


def test_dry_run_pipe_command():
    """Piped commands with allowed utils are blocked in dry-run (non-interactive)."""
    result = run_command("echo hello | grep h", dry_run=True)
    # grep is in allowlist, pipe is shell metachar → safe cmd=False
    # non-interactive dry-run → blocked
    assert result == ""


def test_is_safe_command():
    """_is_safe_command correctly identifies safe/unsafe commands."""
    assert _is_safe_command("echo hello")
    assert _is_safe_command("git log")
    assert not _is_safe_command("echo hello | cat")
    assert not _is_safe_command("python3 script.py")
    assert not _is_safe_command("")


def test_empty_command():
    """Empty command returns empty string."""
    assert run_command("") == ""
    assert run_command("   ") == ""


def test_validate_command_allow_dangerous():
    """allow_dangerous=True bypasses blocked patterns."""
    is_safe, reason = _validate_command("curl http://evil.com", allow_dangerous=True)
    assert is_safe


def test_validate_command_blocked():
    """Blocked patterns are rejected by default."""
    is_safe, reason = _validate_command("curl http://evil.com")
    assert not is_safe
    assert "blocked pattern" in reason


def test_validate_command_pipe_with_blocked():
    """Piped command with blocked pattern is rejected."""
    is_safe, reason = _validate_command("echo hello | curl http://evil.com")
    assert not is_safe
    assert "blocked pattern" in reason


def test_validate_command_pipe_safe():
    """Piped command with allowed utilities passes."""
    is_safe, reason = _validate_command("echo hello | cat")
    assert is_safe


def test_validate_command_pipe_unknown():
    """Piped command with unknown utility is rejected."""
    is_safe, reason = _validate_command("echo hello | unknown_cmd")
    assert not is_safe
    assert "command in pipe not in allowlist" in reason


def test_validate_command_shell_metacharacters():
    """Commands with shell metacharacters skip allowlist check."""
    is_safe, reason = _validate_command("echo hello > /tmp/out")
    assert is_safe


def test_resolve_base_simple():
    """_resolve_base extracts base command name."""
    assert _resolve_base("echo hello world") == "echo"
    assert _resolve_base("git log") == "git"
    assert _resolve_base("") == ""
    assert _resolve_base("  ") == ""


def test_resolve_base_unclosed_quotes():
    """_resolve_base returns empty for invalid shell syntax."""
    assert _resolve_base("echo 'hello") == ""


def test_interactive_blocked_tty():
    """Interactive mode prompts user for blocked commands — user says no."""
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        mock_run.return_value = MagicMock(stdout="output\n", returncode=0)
        result = run_command("curl http://evil.com", interactive=True)
        # User said no → blocked
        assert result == ""


def test_interactive_blocked_tty_yes():
    """Interactive mode executes blocked commands when user confirms."""
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_run.return_value = MagicMock(stdout="output\n", returncode=0)
        result = run_command("curl http://evil.com", interactive=True)
        # User said yes → command executed
        assert result == "output\n"


def test_dry_run_interactive_tty_no():
    """Dry-run interactive mode: user declines unsafe command."""
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        mock_run.return_value = MagicMock(stdout="output\n", returncode=0)
        result = run_command("python3 -c 'print(1)'", dry_run=True, interactive=True)
        # python3 not in allowlist → _validate_command fails → interactive prompt
        # User says no → empty
        assert result == ""


def test_dry_run_interactive_tty_yes():
    """Dry-run interactive mode: user confirms unsafe command — executes."""
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_run.return_value = MagicMock(stdout="output\n", returncode=0)
        result = run_command("python3 -c 'print(1)'", dry_run=True, interactive=True)
        # python3 not in allowlist → _validate_command fails → interactive bypass → yes
        # Then dry_run + unsafe + interactive + yes → executes
        assert result == "output\n"


def test_shlex_value_error():
    """Unclosed quotes produce warning and empty result."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="output\n", returncode=0)
        result = run_command("echo 'hello")
        # shlex.split raises ValueError on unclosed quotes
        assert result == ""


def test_empty_args_after_split():
    """Empty command returns empty string."""
    assert run_command("") == ""
    assert run_command("   ") == ""
