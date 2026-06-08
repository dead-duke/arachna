import subprocess
from unittest.mock import patch

from arachna.runner import (
    _is_safe_command,
    _resolve_base,
    _validate_command,
    run_command,
)


def _completed_process(stdout="", stderr="", returncode=0, args=None):
    return subprocess.CompletedProcess(
        args=args or ["echo", "hello"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_simple():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="hello\n")
        assert run_command("echo hello").strip() == "hello"


def test_with_args():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="hello world\n")
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
        mock_run.return_value = _completed_process(stdout="hello\n")
        assert run_command("echo hello | cat", allow_file_args=True).strip() == "hello"


def test_double_ampersand():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="first\nsecond\n")
        lines = run_command("echo first && echo second", allow_file_args=True).strip().split("\n")
        assert lines == ["first", "second"]


def test_dry_run_safe_command():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="hello\n")
        assert run_command("echo hello", dry_run=True).strip() == "hello"


def test_dry_run_unsafe_command():
    result = run_command("python3 -c 'print(1)'", dry_run=True)
    assert result == ""


def test_dry_run_pipe_command():
    result = run_command("echo hello | grep h", dry_run=True)
    assert result == ""


def test_is_safe_command():
    assert _is_safe_command("echo hello")
    assert _is_safe_command("pwd")
    assert not _is_safe_command("echo hello | cat")
    assert not _is_safe_command("python3 script.py")
    assert not _is_safe_command("")
    # git requires allow_file_args
    assert _is_safe_command("git log", allow_file_args=True)
    assert not _is_safe_command("git log")


def test_empty_command():
    assert run_command("") == ""
    assert run_command("   ") == ""


def test_validate_command_allow_dangerous():
    is_safe, reason = _validate_command("curl http://evil.com", allow_dangerous=True)
    assert is_safe


def test_validate_command_blocked():
    is_safe, reason = _validate_command("curl http://evil.com")
    assert not is_safe
    assert "blocked pattern" in reason


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


def test_interactive_blocked_tty():
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        mock_run.return_value = _completed_process(stdout="output\n")
        result = run_command("curl http://evil.com", interactive=True)
        assert result == ""


def test_interactive_blocked_tty_yes():
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_run.return_value = _completed_process(stdout="output\n")
        result = run_command("curl http://evil.com", interactive=True)
        assert result == "output\n"


def test_dry_run_interactive_tty_no():
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        mock_run.return_value = _completed_process(stdout="output\n")
        result = run_command("python3 -c 'print(1)'", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_interactive_tty_yes():
    with (
        patch("subprocess.run") as mock_run,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_run.return_value = _completed_process(stdout="output\n")
        result = run_command("python3 -c 'print(1)'", dry_run=True, interactive=True)
        assert result == "output\n"


def test_shlex_value_error():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="output\n")
        result = run_command("echo 'hello")
        assert result == ""


def test_empty_args_after_split():
    assert run_command("") == ""
    assert run_command("   ") == ""


def test_audit_log_written(tmp_path, monkeypatch):
    import json

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="hello\n")
        run_command("echo hello")

    log_path = tmp_path / "out" / ".arachna_commands.log"
    assert log_path.exists()
    content = log_path.read_text()
    assert "OK: echo hello" in content


def test_audit_log_blocked(tmp_path, monkeypatch):
    import json

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))

    result = run_command("curl http://evil.com")
    assert result == ""

    log_path = tmp_path / "out" / ".arachna_commands.log"
    assert log_path.exists()
    content = log_path.read_text()
    assert "FAIL: curl http://evil.com" in content


def test_audit_log_no_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="hello\n")
        run_command("echo hello")

    log_path = tmp_path / "arachna_context" / ".arachna_commands.log"
    assert log_path.exists()
