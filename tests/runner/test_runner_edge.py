"""Tests for uncovered branches in runner.py."""

from unittest.mock import MagicMock, patch

from arachna.runner import (
    _is_safe_command,
    run_command,
)


def _mock_popen(stdout=""):
    mock = MagicMock()
    mock.stdout.read.side_effect = [stdout, ""]
    mock.wait.return_value = 0
    return mock


def test_dry_run_unsafe_non_interactive(tmp_path):
    result = run_command("curl http://evil.com", root=tmp_path, dry_run=True)
    assert result == ""


def test_dry_run_unsafe_interactive_no(tmp_path):
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("curl http://evil.com", root=tmp_path, dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_shell_metachar_non_interactive(tmp_path):
    result = run_command("echo hello > /tmp/out", root=tmp_path, dry_run=True)
    assert result == ""


def test_dry_run_shell_metachar_interactive_no(tmp_path):
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("echo hello > /tmp/out", root=tmp_path, dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_shell_metachar_interactive_yes(tmp_path):
    with (
        patch("subprocess.Popen") as mock_popen,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="y"),
    ):
        mock_popen.return_value = _mock_popen(stdout="hello\n")
        result = run_command("echo hello > /tmp/out", root=tmp_path, dry_run=True, interactive=True)
        assert result == "hello\n"


def test_run_command_allow_dangerous_curl(tmp_path):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="output\n")
        result = run_command("curl http://example.com", root=tmp_path, allow_dangerous=True)
        assert result == "output\n"


def test_run_command_allow_dangerous_rm(tmp_path):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="")
        result = run_command("rm -rf /", root=tmp_path, allow_dangerous=True)
        assert result == ""


def test_run_command_empty_after_strip(tmp_path):
    assert run_command("   ", root=tmp_path) == ""


def test_run_command_os_error_on_execution(tmp_path):
    with patch("subprocess.Popen", side_effect=OSError("bad interpreter")):
        result = run_command("some_broken_cmd", root=tmp_path)
        assert result == ""


def test_run_command_value_error_on_execution(tmp_path):
    with patch("subprocess.Popen", side_effect=ValueError("invalid argument")):
        result = run_command("some_cmd", root=tmp_path)
        assert result == ""


def test_is_safe_command_unknown():
    assert not _is_safe_command("python3 script.py")
    assert not _is_safe_command("node server.js")
    assert not _is_safe_command("")


def test_is_safe_command_with_shell_chars():
    assert not _is_safe_command("echo hello | cat")
    assert not _is_safe_command("echo hello > file.txt")
    assert not _is_safe_command("echo hello && echo world")


def test_run_command_shell_double_ampersand(tmp_path):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="a\nb\n")
        result = run_command("echo a && echo b", root=tmp_path, allow_file_args=True)
        assert result == "a\nb\n"


def test_run_command_shell_redirect(tmp_path):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="")
        result = run_command("echo hello > /dev/null", root=tmp_path, allow_file_args=True)
        assert result == ""
