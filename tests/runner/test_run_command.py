import subprocess
from unittest.mock import MagicMock, patch

from arachna.runner import _is_safe_command, run_command


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
    # python3 is not in allowlist, non-interactive → blocked
    assert result == ""


def test_dry_run_pipe_command():
    """Piped commands are blocked in dry-run (non-interactive)."""
    result = run_command("echo hello | grep h", dry_run=True)
    # grep is in allowlist, but pipe makes it unsafe → blocked in dry-run
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
