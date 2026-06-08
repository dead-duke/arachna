"""Tests for run_pre_commands in runner.py (v2.8.2)."""

import subprocess
from unittest.mock import patch

from arachna.runner import run_pre_commands


def _completed_process(stdout="", stderr="", returncode=0, args=None):
    return subprocess.CompletedProcess(
        args=args or ["echo", "hello"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_run_pre_commands_single():
    """Single pre_command returns one result."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _completed_process(stdout="output\n")
        results = run_pre_commands(["echo hello"])
    assert len(results) == 1
    assert results[0][0] == "echo hello"
    assert results[0][1] == "output\n"


def test_run_pre_commands_multiple():
    """Multiple pre_commands return multiple results in order."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            _completed_process(stdout="first\n"),
            _completed_process(stdout="second\n"),
        ]
        results = run_pre_commands(["echo first", "echo second"])
    assert len(results) == 2
    assert results[0][0] == "echo first"
    assert results[0][1] == "first\n"
    assert results[1][0] == "echo second"
    assert results[1][1] == "second\n"


def test_run_pre_commands_empty():
    """Empty list returns empty list."""
    results = run_pre_commands([])
    assert results == []


def test_run_pre_commands_with_delay(monkeypatch):
    """ARACHNA_PRE_COMMAND_DELAY triggers sleep between commands."""
    monkeypatch.setenv("ARACHNA_PRE_COMMAND_DELAY", "0.1")
    import importlib

    import arachna.runner as runner_module

    importlib.reload(runner_module)

    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(runner_module.time, "sleep", fake_sleep)

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            _completed_process(stdout="a\n"),
            _completed_process(stdout="b\n"),
            _completed_process(stdout="c\n"),
        ]
        results = runner_module.run_pre_commands(["cmd1", "cmd2", "cmd3"])

    assert len(results) == 3
    assert len(sleep_calls) == 2  # sleep after 1st and 2nd, not after 3rd
    assert sleep_calls[0] == 0.1


def test_run_pre_commands_no_delay_default():
    """No ARACHNA_PRE_COMMAND_DELAY — no sleep."""
    import importlib

    import arachna.runner as runner_module

    importlib.reload(runner_module)

    with (
        patch("subprocess.run") as mock_run,
        patch.object(runner_module.time, "sleep") as mock_sleep,
    ):
        mock_run.return_value = _completed_process(stdout="x\n")
        runner_module.run_pre_commands(["cmd1", "cmd2"])

    mock_sleep.assert_not_called()
