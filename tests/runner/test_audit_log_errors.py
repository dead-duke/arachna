"""Tests for audit log error handling."""

import json

from arachna.runner import _get_audit_log_path


def test_get_audit_log_path_corrupted_json(tmp_path, monkeypatch):
    """_get_audit_log_path handles corrupted .arachna.json gracefully."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text("not valid json")

    log_path = _get_audit_log_path()
    # Should fall back to arachna_context/ in cwd
    assert log_path is not None
    assert log_path.name == ".arachna_commands.log"


def test_get_audit_log_path_json_decode_error(tmp_path, monkeypatch):
    """_get_audit_log_path handles JSON with trailing garbage."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text('{"output_dir": "custom_out"} extra garbage')

    log_path = _get_audit_log_path()
    assert log_path is not None
    assert log_path.name == ".arachna_commands.log"


def test_get_audit_log_path_no_output_dir_key(tmp_path, monkeypatch):
    """_get_audit_log_path handles JSON without output_dir key."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(json.dumps({"project_name": "test"}))

    log_path = _get_audit_log_path()
    assert log_path is not None
    assert ".arachna_commands.log" in str(log_path)
