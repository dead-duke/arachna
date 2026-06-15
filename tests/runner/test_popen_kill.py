"""Coverage for _run_popen kill path when output exceeds limit."""

from unittest.mock import MagicMock, patch

from arachna.domain.runner import _run_popen


def test_run_popen_kill_on_exceed():
    """Process killed when output exceeds max_output_size."""
    mock_proc = MagicMock()
    mock_proc.stdout.read.side_effect = ["a" * 1000, ""]
    mock_proc.wait.return_value = 0

    with patch("subprocess.Popen", return_value=mock_proc):
        output, was_truncated = _run_popen("echo huge", False, max_output_size=50)

    assert was_truncated
    assert "truncated" in output
    mock_proc.kill.assert_called_once()


def test_run_popen_exact_limit():
    """Output within limit passes through without truncation."""
    mock_proc = MagicMock()
    mock_proc.stdout.read.side_effect = ["hello", ""]
    mock_proc.wait.return_value = 0

    with patch("subprocess.Popen", return_value=mock_proc):
        output, was_truncated = _run_popen("echo hello", False, max_output_size=1000)

    assert not was_truncated
    assert output == "hello"


def test_run_popen_os_error():
    """_run_popen returns empty on OSError."""
    with patch("subprocess.Popen", side_effect=OSError("no such file")):
        output, was_truncated = _run_popen("nonexistent", False, 10000)
    assert output == ""
    assert not was_truncated


def test_run_popen_file_not_found():
    """_run_popen returns empty on FileNotFoundError."""
    with patch("subprocess.Popen", side_effect=FileNotFoundError("not found")):
        output, was_truncated = _run_popen("nonexistent", False, 10000)
    assert output == ""
    assert not was_truncated


def test_run_popen_value_error():
    """_run_popen returns empty on ValueError."""
    with patch("subprocess.Popen", side_effect=ValueError("invalid")):
        output, was_truncated = _run_popen("bad", False, 10000)
    assert output == ""
    assert not was_truncated
