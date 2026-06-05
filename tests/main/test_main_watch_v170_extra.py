"""Extra coverage for __main__.py Watch CLI — v1.7.0 edge cases."""

import json

import pytest

from arachna.__main__ import _cmd_snapshot


def test_cmd_snapshot_info_invalid_id_flag(tmp_path, monkeypatch):
    """--snapshot info with flag-like id exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "info", "--profile"])


def test_cmd_snapshot_info_not_found_error(tmp_path, monkeypatch):
    """--snapshot info for non-existent snapshot exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "info", "nonexistent"])


def test_cmd_snapshot_info_list_snapshots_error(tmp_path, monkeypatch):
    """--snapshot info when list_snapshots raises an exception exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    from unittest.mock import patch

    with (
        patch("arachna.store.list_snapshots", side_effect=OSError("disk error")),
        pytest.raises(SystemExit),
    ):
        _cmd_snapshot(["arachna", "--snapshot", "info", "some-id"])


def test_cmd_snapshot_rename_missing_old(tmp_path, monkeypatch):
    """--snapshot rename without old name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "rename"])


def test_cmd_snapshot_rename_missing_new(tmp_path, monkeypatch):
    """--snapshot rename without new name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "rename", "old-name"])


def test_cmd_snapshot_rename_old_is_flag(tmp_path, monkeypatch):
    """--snapshot rename with flag as old name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "rename", "--profile", "new-name"])


def test_cmd_snapshot_rename_new_is_flag(tmp_path, monkeypatch):
    """--snapshot rename with flag as new name exits 1."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    with pytest.raises(SystemExit):
        _cmd_snapshot(["arachna", "--snapshot", "rename", "old-name", "--profile"])


def test_cmd_snapshot_info_profile_legacy_format(tmp_path, monkeypatch):
    """--snapshot info --profile with legacy string profile format."""
    import json as _json

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".arachna.json").write_text(
        _json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
    )

    from arachna.store import _store_root, write_object

    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    test_hash = write_object(b"legacy content")
    old_manifest = {
        "id": "legacy-prof",
        "name": "legacy-prof",
        "created": "2026-01-01T00:00:00",
        "profile": "code",
        "files": {"a.py": f"sha256:{test_hash}"},
    }
    (snapshots_dir / "legacy-prof.json").write_text(_json.dumps(old_manifest))

    import sys
    from io import StringIO

    out = StringIO()
    old = sys.stdout
    sys.stdout = out
    _cmd_snapshot(["arachna", "--snapshot", "info", "legacy-prof", "--profile"])
    sys.stdout = old

    assert "legacy format" in out.getvalue()
