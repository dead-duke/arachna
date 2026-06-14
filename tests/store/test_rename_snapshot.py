"""Tests for rename_snapshot in store.py (v1.7.0)."""

import pytest

from arachna.store import (
    create_snapshot,
    load_snapshot,
    rename_snapshot,
)
from arachna.store_errors import ObjectNotFoundError, SnapshotExistsError


def test_rename_snapshot_happy_path(tmp_path):
    """rename_snapshot renames manifest, updates id and name."""
    create_snapshot({"a.py": "hello"}, name="old-name", root=tmp_path)
    new_id = rename_snapshot("old-name", "new-name", root=tmp_path)

    assert new_id == "new-name"

    manifest = load_snapshot("new-name", root=tmp_path)
    assert manifest["id"] == "new-name"
    assert manifest["name"] == "new-name"
    assert manifest["files"] == {"a.py": manifest["files"]["a.py"]}

    with pytest.raises(ObjectNotFoundError):
        load_snapshot("old-name", root=tmp_path)


def test_rename_snapshot_updates_head(tmp_path):
    """rename_snapshot updates HEAD when it pointed to old_id."""
    create_snapshot({"a.py": "x"}, name="head-snap", root=tmp_path)
    rename_snapshot("head-snap", "renamed-head", root=tmp_path)

    from arachna.store import _store_root

    head = (_store_root(tmp_path) / "HEAD").read_text().strip()
    assert head == "renamed-head"


def test_rename_snapshot_duplicate_name(tmp_path):
    """rename_snapshot raises SnapshotExistsError when new_id already exists."""
    create_snapshot({"a.py": "x"}, name="first", root=tmp_path)
    create_snapshot({"b.py": "y"}, name="second", root=tmp_path)

    with pytest.raises(SnapshotExistsError, match="already exists"):
        rename_snapshot("first", "second", root=tmp_path)


def test_rename_snapshot_not_found(tmp_path):
    """rename_snapshot raises ObjectNotFoundError when old_id doesn't exist."""
    with pytest.raises(ObjectNotFoundError, match="not found"):
        rename_snapshot("nonexistent", "new-name", root=tmp_path)


def test_rename_snapshot_other_head_unchanged(tmp_path):
    """rename_snapshot does not update HEAD when it points to a different snapshot."""
    create_snapshot({"a.py": "x"}, name="snap-a", root=tmp_path)
    create_snapshot({"b.py": "y"}, name="snap-b", root=tmp_path)

    rename_snapshot("snap-a", "renamed-a", root=tmp_path)

    from arachna.store import _store_root

    head = (_store_root(tmp_path) / "HEAD").read_text().strip()
    assert head == "snap-b"


def test_rename_snapshot_objects_preserved(tmp_path):
    """rename_snapshot preserves objects — content still accessible after rename."""
    sid = create_snapshot({"a.py": "hello world"}, name="original", root=tmp_path)
    old_manifest = load_snapshot(sid, root=tmp_path)
    old_hash = old_manifest["files"]["a.py"]

    rename_snapshot("original", "renamed", root=tmp_path)

    new_manifest = load_snapshot("renamed", root=tmp_path)
    assert new_manifest["files"]["a.py"] == old_hash


def test_rename_snapshot_preserves_all_fields(tmp_path):
    """rename_snapshot preserves profile, pre_commands, command, created."""
    profile_dict = {"directories": ["src"], "patterns": ["*.py"]}
    create_snapshot(
        {"a.py": "x"},
        profile_dict=profile_dict,
        name="full-snap",
        pre_commands={"pre: echo": "sha256:abc123"},
        command={"command output": "sha256:def456"},
        root=tmp_path,
    )

    rename_snapshot("full-snap", "renamed-full", root=tmp_path)

    manifest = load_snapshot("renamed-full", root=tmp_path)
    assert manifest["profile"] == profile_dict
    assert manifest["pre_commands"] == {"pre: echo": "sha256:abc123"}
    assert manifest["command"] == {"command output": "sha256:def456"}
    assert "created" in manifest
