import subprocess
from unittest.mock import MagicMock, patch

from arachna.runner import run_command


def test_simple():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="hello\n", returncode=0)
        assert run_command("echo hello").strip() == "hello"


def test_with_args():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="hello world\n", returncode=0)
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
        mock_run.return_value = MagicMock(stdout="hello\n", returncode=0)
        assert run_command("echo hello | cat").strip() == "hello"


def test_double_ampersand():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="first\nsecond\n", returncode=0)
        lines = run_command("echo first && echo second").strip().split("\n")
        assert lines == ["first", "second"]
