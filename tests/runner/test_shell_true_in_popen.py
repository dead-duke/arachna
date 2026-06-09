"""TEST-01: shell=True verified in Popen calls (v2.9.2)."""

from unittest.mock import MagicMock, patch

from arachna.runner import run_command


def test_pipe_uses_shell_true():
    """Piped commands pass shell=True to Popen."""
    mock = MagicMock()
    mock.stdout.read.side_effect = ["output\n", ""]
    mock.wait.return_value = 0
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = mock
        run_command("echo hello | cat", allow_file_args=True)
        mock_popen.assert_called_with(
            "echo hello | cat", stdout=-1, stderr=-2, shell=True, text=True
        )


def test_simple_uses_shell_false():
    """Simple commands pass shell=False to Popen."""
    mock = MagicMock()
    mock.stdout.read.side_effect = ["output\n", ""]
    mock.wait.return_value = 0
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = mock
        run_command("echo hello")
        mock_popen.assert_called_with(["echo", "hello"], stdout=-1, stderr=-2, text=True)
