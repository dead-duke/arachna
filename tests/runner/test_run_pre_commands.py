"""Tests for run_pre_commands in runner.py (v2.8.2)."""

from unittest.mock import MagicMock, patch

from arachna.runner import run_pre_commands


def _mock_popen(stdout=""):
    mock = MagicMock()
    mock.stdout.read.side_effect = [stdout, ""]
    mock.wait.return_value = 0
    return mock


def test_run_pre_commands_single():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = _mock_popen(stdout="output\n")
        results = run_pre_commands(["echo hello"])
    assert len(results) == 1
    assert results[0][0] == "echo hello"
    assert results[0][1] == "output\n"


def test_run_pre_commands_multiple():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.side_effect = [
            _mock_popen(stdout="first\n"),
            _mock_popen(stdout="second\n"),
        ]
        results = run_pre_commands(["echo first", "echo second"])
    assert len(results) == 2
    assert results[0][0] == "echo first"
    assert results[0][1] == "first\n"
    assert results[1][0] == "echo second"
    assert results[1][1] == "second\n"


def test_run_pre_commands_empty():
    results = run_pre_commands([])
    assert results == []


def test_run_pre_commands_with_delay(monkeypatch):
    monkeypatch.setenv("ARACHNA_PRE_COMMAND_DELAY", "0.1")
    import importlib

    import arachna.runner as runner_module

    importlib.reload(runner_module)

    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(runner_module.time, "sleep", fake_sleep)

    with patch("subprocess.Popen") as mock_popen:
        mock_popen.side_effect = [
            _mock_popen(stdout="a\n"),
            _mock_popen(stdout="b\n"),
            _mock_popen(stdout="c\n"),
        ]
        results = runner_module.run_pre_commands(["cmd1", "cmd2", "cmd3"])

    assert len(results) == 3
    assert len(sleep_calls) == 2
    assert sleep_calls[0] == 0.1


def test_run_pre_commands_no_delay_default():
    import importlib

    import arachna.runner as runner_module

    importlib.reload(runner_module)

    with (
        patch("subprocess.Popen") as mock_popen,
        patch.object(runner_module.time, "sleep") as mock_sleep,
    ):
        mock_popen.return_value = _mock_popen(stdout="x\n")
        runner_module.run_pre_commands(["cmd1", "cmd2"])

    mock_sleep.assert_not_called()
