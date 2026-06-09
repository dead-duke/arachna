"""Coverage for dry-run + interactive branches in runner.py."""

from unittest.mock import MagicMock, patch

from arachna.runner import run_command


def _mock_popen(stdout=""):
    mock = MagicMock()
    mock.stdout.read.side_effect = [stdout, ""]
    mock.wait.return_value = 0
    return mock


def test_dry_run_safe_executes():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="hello\n")
        result = run_command("echo hello", dry_run=True)
        assert result == "hello\n"


def test_dry_run_unsafe_blocked_non_interactive():
    result = run_command("python3 -c 'print(1)'", dry_run=True)
    assert result == ""


def test_dry_run_unsafe_interactive_no():
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("python3 -c 'print(1)'", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_unsafe_interactive_yes():
    with (
        patch("subprocess.Popen") as mock_popen,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_popen.return_value = _mock_popen(stdout="output\n")
        result = run_command("python3 -c 'print(1)'", dry_run=True, interactive=True)
        assert result == "output\n"


def test_dry_run_shell_metachar_non_interactive():
    result = run_command("echo hello > /tmp/out", dry_run=True)
    assert result == ""


def test_dry_run_shell_metachar_interactive_no():
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("echo hello > /tmp/out", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_shell_metachar_interactive_yes():
    with (
        patch("subprocess.Popen") as mock_popen,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_popen.return_value = _mock_popen(stdout="hello\n")
        result = run_command("echo hello > /tmp/out", dry_run=True, interactive=True)
        assert result == "hello\n"


def test_dry_run_blocked_by_validate():
    result = run_command("curl http://evil.com", dry_run=True)
    assert result == ""


def test_dry_run_blocked_interactive_no():
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="n"),
    ):
        result = run_command("curl http://evil.com", dry_run=True, interactive=True)
        assert result == ""


def test_dry_run_blocked_interactive_yes():
    with (
        patch("subprocess.Popen") as mock_popen,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_popen.return_value = _mock_popen(stdout="output\n")
        result = run_command("curl http://evil.com", dry_run=True, interactive=True)
        assert result == "output\n"


def test_dry_run_pipe_unsafe_prints_message():
    result = run_command("echo hello | cat", dry_run=True)
    assert result == ""
