"""Tests for rename_snapshot in store.py (v1.7.0)."""

import pytest

from arachna.store import (
    create_snapshot,
    load_snapshot,
    rename_snapshot,
)
from arachna.store_errors import ObjectNotFoundError, SnapshotExistsError


def test_rename_snapshot_happy_path(tmp_path, monkeypatch):
    """rename_snapshot renames manifest, updates id and name."""
    monkeypatch.chdir(tmp_path)

    create_snapshot({"a.py": "hello"}, name="old-name")
    new_id = rename_snapshot("old-name", "new-name")

    assert new_id == "new-name"

    manifest = load_snapshot("new-name")
    assert manifest["id"] == "new-name"
    assert manifest["name"] == "new-name"
    assert manifest["files"] == {"a.py": manifest["files"]["a.py"]}

    # Old name should not exist
    with pytest.raises(ObjectNotFoundError):
        load_snapshot("old-name")


def test_rename_snapshot_updates_head(tmp_path, monkeypatch):
    """rename_snapshot updates HEAD when it pointed to old_id."""
    monkeypatch.chdir(tmp_path)

    create_snapshot({"a.py": "x"}, name="head-snap")
    rename_snapshot("head-snap", "renamed-head")

    from arachna.store import _store_root

    head = (_store_root() / "HEAD").read_text().strip()
    assert head == "renamed-head"


def test_rename_snapshot_duplicate_name(tmp_path, monkeypatch):
    """rename_snapshot raises SnapshotExistsError when new_id already exists."""
    monkeypatch.chdir(tmp_path)

    create_snapshot({"a.py": "x"}, name="first")
    create_snapshot({"b.py": "y"}, name="second")

    with pytest.raises(SnapshotExistsError, match="already exists"):
        rename_snapshot("first", "second")

    # Verify nothing was changed
    assert load_snapshot("first")["id"] == "first"
    assert load_snapshot("second")["id"] == "second"


def test_rename_snapshot_not_found(tmp_path, monkeypatch):
    """rename_snapshot raises ObjectNotFoundError when old_id doesn't exist."""
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ObjectNotFoundError, match="not found"):
        rename_snapshot("nonexistent", "new-name")


def test_rename_snapshot_other_head_unchanged(tmp_path, monkeypatch):
    """rename_snapshot does not update HEAD when it points to a different snapshot."""
    monkeypatch.chdir(tmp_path)

    create_snapshot({"a.py": "x"}, name="snap-a")
    create_snapshot({"b.py": "y"}, name="snap-b")

    # HEAD now points to snap-b (latest)
    rename_snapshot("snap-a", "renamed-a")

    from arachna.store import _store_root

    head = (_store_root() / "HEAD").read_text().strip()
    # HEAD should still point to snap-b
    assert head == "snap-b"


def test_rename_snapshot_objects_preserved(tmp_path, monkeypatch):
    """rename_snapshot preserves objects — content still accessible after rename."""
    monkeypatch.chdir(tmp_path)

    sid = create_snapshot({"a.py": "hello world"}, name="original")
    old_manifest = load_snapshot(sid)
    old_hash = old_manifest["files"]["a.py"]

    rename_snapshot("original", "renamed")

    new_manifest = load_snapshot("renamed")
    assert new_manifest["files"]["a.py"] == old_hash


def test_rename_snapshot_preserves_all_fields(tmp_path, monkeypatch):
    """rename_snapshot preserves profile, pre_commands, command, created."""
    monkeypatch.chdir(tmp_path)

    profile_dict = {"directories": ["src"], "patterns": ["*.py"]}
    create_snapshot(
        {"a.py": "x"},
        profile_dict=profile_dict,
        name="full-snap",
        pre_commands={"pre: echo": "sha256:abc123"},
        command={"command output": "sha256:def456"},
    )

    rename_snapshot("full-snap", "renamed-full")

    manifest = load_snapshot("renamed-full")
    assert manifest["profile"] == profile_dict
    assert manifest["pre_commands"] == {"pre: echo": "sha256:abc123"}
    assert manifest["command"] == {"command output": "sha256:def456"}
    assert "created" in manifest
