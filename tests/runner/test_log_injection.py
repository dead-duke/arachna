"""TC-177: Log injection — newlines in cmd sanitized in audit log."""

import json

from arachna.runner import run_command


def test_newline_in_command_sanitized(tmp_path, monkeypatch):
    """Newlines in command are replaced with \\n in audit log."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))

    import subprocess
    from unittest.mock import patch

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo"], returncode=0, stdout="output\n", stderr=""
        )
        run_command("echo hello\nevil")

    log_path = tmp_path / "out" / ".arachna_commands.log"
    assert log_path.exists()
    content = log_path.read_text()
    # Should be exactly one line — newlines sanitized
    lines = content.strip().split("\n")
    assert len(lines) == 1, f"Expected 1 log line, got {len(lines)}: {lines}"
    assert "\\n" in content
    assert "\nevil" not in content


def test_carriage_return_sanitized(tmp_path, monkeypatch):
    """Carriage returns in command are replaced with \\r in audit log."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"output_dir": "out"}))

    import subprocess
    from unittest.mock import patch

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo"], returncode=0, stdout="output\n", stderr=""
        )
        run_command("echo hello\revil")

    log_path = tmp_path / "out" / ".arachna_commands.log"
    content = log_path.read_text()
    assert "\\r" in content
