"""Coverage for _run_popen with shell=True path."""

from unittest.mock import MagicMock, patch

from arachna.domain.runner import _run_popen


def test_run_popen_shell_true():
    """_run_popen with needs_shell=True uses shell=True in Popen."""
    mock_proc = MagicMock()
    mock_proc.stdout.read.side_effect = ["output\n", ""]
    mock_proc.wait.return_value = 0

    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = mock_proc
        output, was_truncated = _run_popen("echo hello | cat", True, 10000)

    assert output == "output\n"
    assert not was_truncated
    mock_popen.assert_called_with("echo hello | cat", stdout=-1, stderr=-2, shell=True, text=True)


def test_run_popen_shell_true_with_args():
    """_run_popen with needs_shell=False uses shlex.split."""
    mock_proc = MagicMock()
    mock_proc.stdout.read.side_effect = ["hi\n", ""]
    mock_proc.wait.return_value = 0

    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = mock_proc
        output, was_truncated = _run_popen("echo hello", False, 10000)

    assert output == "hi\n"
    mock_popen.assert_called_with(["echo", "hello"], stdout=-1, stderr=-2, text=True)
