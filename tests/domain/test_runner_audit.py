"""Tests for runner.py audit log edge cases."""

from unittest.mock import patch

import arachna.domain.runner as runner_mod
from arachna.domain.runner import _write_log, run_command


def test_get_audit_log_path_os_error(tmp_path):
    """_get_audit_log_path catches OSError from Path.exists()."""
    (tmp_path / ".arachna.json").write_text("{}")
    with patch("pathlib.Path.exists", side_effect=OSError("permission denied")):
        result = runner_mod._get_audit_log_path(tmp_path)
        assert result is None


def test_write_log_custom_writer(tmp_path):
    """_write_log uses custom log_writer when passed as parameter."""
    calls = []

    def custom_writer(path, entry):
        calls.append((str(path), entry))

    _write_log(tmp_path / "test.log", "entry1", log_writer=custom_writer)

    assert len(calls) == 1
    assert calls[0][1] == "entry1"


def test_write_log_os_error(tmp_path):
    """_write_log handles OSError on write gracefully."""
    log_path = tmp_path / "sub" / "test.log"
    with patch("pathlib.Path.mkdir", side_effect=OSError("no space")):
        _write_log(log_path, "entry")


def test_log_command_no_audit_path(tmp_path):
    """_log_command when _get_audit_log_path returns None."""
    with patch.object(runner_mod, "_get_audit_log_path", return_value=None):
        runner_mod._log_command("echo test", True, tmp_path)


def test_run_command_with_custom_log_writer(tmp_path):
    """run_command passes log_writer through to audit logging."""
    import json

    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    calls = []

    def custom_writer(path, entry):
        calls.append((str(path), entry))

    with patch("subprocess.Popen") as mp:
        from tests.conftest import mock_popen

        mp.return_value = mock_popen(stdout="hello\n")
        run_command("echo hello", root=tmp_path, log_writer=custom_writer)

    assert len(calls) == 1
    assert "OK: echo hello" in calls[0][1]
