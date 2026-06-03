"""Coverage for dry-run + interactive branches in runner.py."""

import subprocess
from unittest.mock import patch

from arachna.runner import run_command


def _completed_process(stdout="", stderr="", returncode=0, args=None):
    return subprocess.CompletedProcess(
        args=args or ["echo", "hello"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_dry_run_safe_executes():
    """Safe commands execute even in dry-run mode."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="hello\n")
        result = run_command("echo hello", dry_run=True)
        assert result == "hello\n"


def test_dry_run_unsafe_blocked_non_interactive():
    """Unsafe command in dry-run non-interactive returns empty."""
    result = run_command("python3 -c 'print(1)'", dry_run=True)
    assert result == ""


def test_dry_run_unsafe_interactive_no():
    """Dry-run unsafe interactive: user declines."""
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("python3 -c 'print(1)'", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_unsafe_interactive_yes():
    """Dry-run unsafe interactive: user confirms — executes."""
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_run.return_value = _completed_process(stdout="output\n")
        result = run_command("python3 -c 'print(1)'", dry_run=True, interactive=True)
        assert result == "output\n"


def test_dry_run_shell_metachar_non_interactive():
    """Command with shell metachar in dry-run non-interactive returns empty."""
    result = run_command("echo hello > /tmp/out", dry_run=True)
    assert result == ""


def test_dry_run_shell_metachar_interactive_no():
    """Dry-run shell metachar interactive: user declines."""
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("echo hello > /tmp/out", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_shell_metachar_interactive_yes():
    """Dry-run shell metachar interactive: user confirms — executes."""
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_run.return_value = _completed_process(stdout="hello\n")
        result = run_command("echo hello > /tmp/out", dry_run=True, interactive=True)
        assert result == "hello\n"


def test_dry_run_blocked_by_validate():
    """curl is blocked by _validate_command before dry-run check."""
    result = run_command("curl http://evil.com", dry_run=True)
    assert result == ""


def test_dry_run_blocked_interactive_no():
    """Blocked command in dry-run interactive: user declines."""
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("curl http://evil.com", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_blocked_interactive_yes():
    """Blocked command in dry-run interactive: user confirms — executes."""
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_run.return_value = _completed_process(stdout="output\n")
        result = run_command("curl http://evil.com", dry_run=True, interactive=True)
        assert result == "output\n"


def test_dry_run_pipe_unsafe_prints_message():
    """Pipe with safe commands but shell metachar → dry-run prints warning, returns empty."""
    result = run_command("echo hello | cat", dry_run=True)
    # Shell metachar + not _is_safe_command → prints [DRY-RUN] and returns ""
    assert result == ""
