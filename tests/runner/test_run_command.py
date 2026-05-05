import subprocess
from unittest.mock import patch

from arachna.runner import run_command


def test_simple():
    assert run_command("echo hello").strip() == "hello"


def test_with_args():
    assert run_command("echo hello world").strip() == "hello world"


def test_nonexistent():
    assert run_command("nonexistent_cmd_xyz") == ""


def test_timeout():
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="sleep", timeout=1)):
        assert run_command("sleep 10") == ""


def test_os_error():
    with patch("subprocess.run", side_effect=OSError("wrong interpreter")):
        assert run_command("bad") == ""


def test_pipe():
    assert run_command("echo hello | cat").strip() == "hello"


def test_double_ampersand():
    lines = run_command("echo first && echo second").strip().split("\n")
    assert lines == ["first", "second"]
