"""Tests for max_output_size in runner.py (v2.9.2)."""

from unittest.mock import MagicMock, patch

from arachna.domain.runner import _run_popen, run_command


def _mock_popen_chunks(chunks):
    mock = MagicMock()
    mock.stdout.read.side_effect = chunks + [""]
    mock.wait.return_value = 0
    return mock


def test_max_output_size_truncation():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen_chunks(["a" * 5000, "b" * 5000])
        output, was_truncated = _run_popen("echo test", False, 7000)
    assert was_truncated
    assert "truncated" in output
    assert len(output) <= 7500


def test_max_output_size_within_limit():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen_chunks(["hello\n"])
        output, was_truncated = _run_popen("echo hello", False, 10000)
    assert not was_truncated
    assert output == "hello\n"


def test_run_command_truncation_warning(tmp_path):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen_chunks(["a" * 100])
        result = run_command("echo huge output", root=tmp_path, max_output_size=5)
    assert "truncated" in result
