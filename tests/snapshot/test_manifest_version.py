"""Tests for _version field in snapshot manifests — migration and future version rejection."""

import json

import pytest

from arachna.snapshot.store import _store_root, create_snapshot, load_snapshot


def test_new_snapshot_has_version_field(tmp_path):
    """Snapshots created now include _version field."""
    sid = create_snapshot({"a.py": "hello"}, name="version-test", root=tmp_path)
    manifest = load_snapshot(sid, root=tmp_path)
    assert "_version" in manifest
    assert manifest["_version"] == 1


def test_old_manifest_without_version_still_loads(tmp_path):
    """Snapshot without _version field (v0 format) is migrated to v1 on load."""
    store_dir = _store_root(tmp_path)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    old_manifest = {
        "id": "old-snap",
        "name": "old-snap",
        "created": "2026-01-01T00:00:00",
        "profile": {},
        "files": {},
    }
    (snapshots_dir / "old-snap.json").write_text(json.dumps(old_manifest))

    manifest = load_snapshot("old-snap", root=tmp_path)
    assert manifest["_version"] == 1


def test_future_version_rejected(tmp_path):
    """Snapshot with version newer than supported raises ValueError."""
    store_dir = _store_root(tmp_path)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    future_manifest = {
        "_version": 999,
        "id": "future-snap",
        "name": "future-snap",
        "created": "2026-01-01T00:00:00",
        "profile": {},
        "files": {},
    }
    (snapshots_dir / "future-snap.json").write_text(json.dumps(future_manifest))

    with pytest.raises(ValueError, match="newer than supported"):
        load_snapshot("future-snap", root=tmp_path)


def test_migration_preserves_all_fields(tmp_path):
    """Migration from v0 to v1 keeps id, name, created, profile, files intact."""
    store_dir = _store_root(tmp_path)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    old_manifest = {
        "id": "migrate-me",
        "name": "migrate-me",
        "created": "2026-06-01T12:00:00",
        "profile": {"directories": ["src"]},
        "files": {"src/main.py": "sha256:abc123"},
    }
    (snapshots_dir / "migrate-me.json").write_text(json.dumps(old_manifest))

    manifest = load_snapshot("migrate-me", root=tmp_path)
    assert manifest["id"] == "migrate-me"
    assert manifest["name"] == "migrate-me"
    assert manifest["created"] == "2026-06-01T12:00:00"
    assert manifest["profile"] == {"directories": ["src"]}
    assert manifest["files"] == {"src/main.py": "sha256:abc123"}
    assert manifest["_version"] == 1
