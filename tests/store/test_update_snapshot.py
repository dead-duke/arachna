"""Tests for update_snapshot in store.py (v1.6.4)."""

import pytest

from arachna.store import (
    create_snapshot,
    load_snapshot,
    update_snapshot,
)
from arachna.store_errors import ObjectNotFoundError


def test_update_snapshot_updates_files(tmp_path, monkeypatch):
    """update_snapshot replaces file hashes."""
    monkeypatch.chdir(tmp_path)

    create_snapshot({"a.py": "original"}, name="update-test")
    update_snapshot("update-test", {"a.py": "modified", "b.py": "new file"})

    manifest = load_snapshot("update-test")
    assert len(manifest["files"]) == 2
    assert "a.py" in manifest["files"]
    assert "b.py" in manifest["files"]


def test_update_snapshot_updates_timestamp(tmp_path, monkeypatch):
    """update_snapshot updates created timestamp."""
    monkeypatch.chdir(tmp_path)
    import time

    create_snapshot({"a.py": "x"}, name="ts-test")
    old_manifest = load_snapshot("ts-test")
    old_created = old_manifest["created"]

    time.sleep(0.01)
    update_snapshot("ts-test", {"a.py": "y"})

    new_manifest = load_snapshot("ts-test")
    assert new_manifest["created"] != old_created


def test_update_snapshot_updates_profile(tmp_path, monkeypatch):
    """update_snapshot updates stored profile dict."""
    monkeypatch.chdir(tmp_path)

    profile = {"directories": ["src"], "patterns": ["*.py"]}
    create_snapshot({"a.py": "x"}, profile_dict=profile, name="profile-test")

    new_profile = {"directories": ["lib"], "patterns": ["*.rs"]}
    update_snapshot("profile-test", {"a.py": "x"}, profile_dict=new_profile)

    manifest = load_snapshot("profile-test")
    stored = manifest["profile"]
    assert stored["directories"] == ["lib"]
    assert stored["patterns"] == ["*.rs"]


def test_update_snapshot_keeps_profile_when_none(tmp_path, monkeypatch):
    """update_snapshot keeps existing profile when profile_dict is None."""
    monkeypatch.chdir(tmp_path)

    profile = {"directories": ["src"], "patterns": ["*.py"]}
    create_snapshot({"a.py": "x"}, profile_dict=profile, name="keep-profile")

    update_snapshot("keep-profile", {"b.py": "y"}, profile_dict=None)

    manifest = load_snapshot("keep-profile")
    stored = manifest["profile"]
    assert stored["directories"] == ["src"]


def test_update_snapshot_not_found(tmp_path, monkeypatch):
    """update_snapshot raises ObjectNotFoundError for non-existent snapshot."""
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ObjectNotFoundError):
        update_snapshot("nonexistent", {"a.py": "x"})


def test_update_snapshot_updates_head(tmp_path, monkeypatch):
    """update_snapshot keeps HEAD pointing to updated snapshot."""
    monkeypatch.chdir(tmp_path)

    create_snapshot({"a.py": "x"}, name="head-update")
    update_snapshot("head-update", {"b.py": "y"})

    from arachna.store import _store_root

    head = (_store_root() / "HEAD").read_text().strip()
    assert head == "head-update"


def test_update_snapshot_removes_pre_commands(tmp_path, monkeypatch):
    """update_snapshot removes pre_commands when None passed."""
    monkeypatch.chdir(tmp_path)

    create_snapshot(
        {"a.py": "x"},
        name="pre-remove",
        pre_commands={"pre: echo": "sha256:abc123"},
    )
    update_snapshot("pre-remove", {"a.py": "x"}, pre_commands=None)

    manifest = load_snapshot("pre-remove")
    assert "pre_commands" not in manifest


def test_update_snapshot_removes_command(tmp_path, monkeypatch):
    """update_snapshot removes command when None passed."""
    monkeypatch.chdir(tmp_path)

    create_snapshot(
        {"a.py": "x"},
        name="cmd-remove",
        command={"command output": "sha256:abc123"},
    )
    update_snapshot("cmd-remove", {"a.py": "x"}, command=None)

    manifest = load_snapshot("cmd-remove")
    assert "command" not in manifest
