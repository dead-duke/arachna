"""Tests for update_snapshot in store.py (v1.6.4)."""

import pytest

from arachna.watch.store import (
    create_snapshot,
    load_snapshot,
    update_snapshot,
)
from arachna.watch.store_errors import ObjectNotFoundError


def test_update_snapshot_updates_files(tmp_path):
    create_snapshot({"a.py": "original"}, name="update-test", root=tmp_path)
    update_snapshot("update-test", {"a.py": "modified", "b.py": "new file"}, root=tmp_path)
    manifest = load_snapshot("update-test", root=tmp_path)
    assert len(manifest["files"]) == 2
    assert "a.py" in manifest["files"]
    assert "b.py" in manifest["files"]


def test_update_snapshot_updates_timestamp(tmp_path):
    import time

    create_snapshot({"a.py": "x"}, name="ts-test", root=tmp_path)
    old_manifest = load_snapshot("ts-test", root=tmp_path)
    old_created = old_manifest["created"]
    time.sleep(0.01)
    update_snapshot("ts-test", {"a.py": "y"}, root=tmp_path)
    new_manifest = load_snapshot("ts-test", root=tmp_path)
    assert new_manifest["created"] != old_created


def test_update_snapshot_updates_profile(tmp_path):
    profile = {"directories": ["src"], "patterns": ["*.py"]}
    create_snapshot({"a.py": "x"}, profile_dict=profile, name="profile-test", root=tmp_path)
    new_profile = {"directories": ["lib"], "patterns": ["*.rs"]}
    update_snapshot("profile-test", {"a.py": "x"}, profile_dict=new_profile, root=tmp_path)
    manifest = load_snapshot("profile-test", root=tmp_path)
    stored = manifest["profile"]
    assert stored["directories"] == ["lib"]
    assert stored["patterns"] == ["*.rs"]


def test_update_snapshot_keeps_profile_when_none(tmp_path):
    profile = {"directories": ["src"], "patterns": ["*.py"]}
    create_snapshot({"a.py": "x"}, profile_dict=profile, name="keep-profile", root=tmp_path)
    update_snapshot("keep-profile", {"b.py": "y"}, profile_dict=None, root=tmp_path)
    manifest = load_snapshot("keep-profile", root=tmp_path)
    stored = manifest["profile"]
    assert stored["directories"] == ["src"]


def test_update_snapshot_not_found(tmp_path):
    with pytest.raises(ObjectNotFoundError):
        update_snapshot("nonexistent", {"a.py": "x"}, root=tmp_path)


def test_update_snapshot_updates_head(tmp_path):
    create_snapshot({"a.py": "x"}, name="head-update", root=tmp_path)
    update_snapshot("head-update", {"b.py": "y"}, root=tmp_path)
    from arachna.watch.store import _store_root

    head = (_store_root(tmp_path) / "HEAD").read_text().strip()
    assert head == "head-update"


def test_update_snapshot_removes_pre_commands(tmp_path):
    create_snapshot(
        {"a.py": "x"}, name="pre-remove", pre_commands={"pre: echo": "sha256:abc123"}, root=tmp_path
    )
    update_snapshot("pre-remove", {"a.py": "x"}, pre_commands=None, root=tmp_path)
    manifest = load_snapshot("pre-remove", root=tmp_path)
    assert "pre_commands" not in manifest


def test_update_snapshot_removes_command(tmp_path):
    create_snapshot(
        {"a.py": "x"}, name="cmd-remove", command={"command output": "sha256:abc123"}, root=tmp_path
    )
    update_snapshot("cmd-remove", {"a.py": "x"}, command=None, root=tmp_path)
    manifest = load_snapshot("cmd-remove", root=tmp_path)
    assert "command" not in manifest
