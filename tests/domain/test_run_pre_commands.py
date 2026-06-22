"""Tests for run_pre_commands — single, multiple, delay, failure handling."""

from unittest.mock import patch

from arachna.domain.execution.runner import run_pre_commands
from tests.conftest import make_popen_mock


def test_run_pre_commands_single(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="output\n")
        results = run_pre_commands(["echo hello"], root=tmp_path)
    assert len(results) == 1
    assert results[0][0] == "echo hello"
    assert results[0][1] == "output\n"


def test_run_pre_commands_multiple(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.side_effect = [
            make_popen_mock(stdout="first\n"),
            make_popen_mock(stdout="second\n"),
        ]
        results = run_pre_commands(["echo first", "echo second"], root=tmp_path)
    assert len(results) == 2
    assert results[0][0] == "echo first"
    assert results[0][1] == "first\n"
    assert results[1][0] == "echo second"
    assert results[1][1] == "second\n"


def test_run_pre_commands_empty(tmp_path):
    results = run_pre_commands([], root=tmp_path)
    assert results == []


def test_run_pre_commands_with_delay(tmp_path):
    with (
        patch("subprocess.Popen") as mp,
        patch("arachna.domain.execution.runner.time.sleep") as mock_sleep,
    ):
        mp.side_effect = [
            make_popen_mock(stdout="a\n"),
            make_popen_mock(stdout="b\n"),
            make_popen_mock(stdout="c\n"),
        ]
        results = run_pre_commands(
            ["echo a", "echo b", "echo c"], root=tmp_path, pre_command_delay=0.1
        )

    assert len(results) == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(0.1)


def test_run_pre_commands_no_delay_default(tmp_path):
    with (
        patch("subprocess.Popen") as mp,
        patch("arachna.domain.execution.runner.time.sleep") as mock_sleep,
    ):
        mp.side_effect = [
            make_popen_mock(stdout="x\n"),
            make_popen_mock(stdout="y\n"),
        ]
        run_pre_commands(["echo x", "echo y"], root=tmp_path)

    mock_sleep.assert_not_called()


def test_run_pre_commands_failure_continues(tmp_path):
    with patch("subprocess.Popen", side_effect=OSError("command not found")):
        results = run_pre_commands(["bad_cmd", "echo ok"], root=tmp_path)
    assert len(results) == 2
    assert results[0][0] == "bad_cmd"
    assert results[0][1] == ""
    assert results[1][0] == "echo ok"


def test_run_pre_commands_partial_failure_middle(tmp_path):
    with patch("subprocess.Popen") as mp:
        mp.side_effect = [
            make_popen_mock(stdout="first\n"),
            OSError("middle failed"),
            make_popen_mock(stdout="third\n"),
        ]
        results = run_pre_commands(["echo first", "echo middle", "echo third"], root=tmp_path)
    assert len(results) == 3
    assert results[0][1] == "first\n"
    assert results[1][1] == ""
    assert results[2][1] == "third\n"
