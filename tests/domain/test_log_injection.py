"""Log injection prevention — newlines in cmd sanitized in audit log."""

import json
from unittest.mock import patch

from arachna.domain.execution.runner import run_command
from tests.conftest import make_popen_mock


def test_newline_in_command_sanitized(tmp_path):
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="output\n")
        run_command("echo hello\nevil", root=tmp_path)

    log_path = tmp_path / "out" / ".arachna_commands.log"
    assert log_path.exists()
    content = log_path.read_text()
    lines = content.strip().split("\n")
    assert len(lines) == 1, f"Expected 1 log line, got {len(lines)}: {lines}"
    assert "\\n" in content
    assert "\nevil" not in content


def test_carriage_return_sanitized(tmp_path):
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))
    with patch("subprocess.Popen") as mp:
        mp.return_value = make_popen_mock(stdout="output\n")
        run_command("echo hello\revil", root=tmp_path)

    log_path = tmp_path / "out" / ".arachna_commands.log"
    content = log_path.read_text()
    assert "\\r" in content
