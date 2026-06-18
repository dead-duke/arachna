"""Tests for the content-addressable store."""

import pytest

from arachna.snapshot.store import (
    create_snapshot,
    delete_snapshot,
    gc,
    list_snapshots,
    load_snapshot,
    read_object,
    stats,
    write_object,
)
from arachna.snapshot.store_errors import CorruptedStoreError, ObjectNotFoundError


def test_write_and_read_object_roundtrip(tmp_path):
    data = b"hello world"
    obj_hash = write_object(data, root=tmp_path)
    result = read_object(obj_hash, root=tmp_path)
    assert result == data


def test_write_object_deduplication(tmp_path):
    h1 = write_object(b"same content", root=tmp_path)
    h2 = write_object(b"same content", root=tmp_path)
    assert h1 == h2
    objects_dir = tmp_path / ".arachna" / "store" / "objects"
    obj_files = list(objects_dir.rglob("*"))
    file_count = sum(1 for f in obj_files if f.is_file())
    assert file_count == 1


def test_write_object_compresses_large_repeated(tmp_path):
    data = b"A" * 10000
    obj_hash = write_object(data, root=tmp_path)
    from arachna.snapshot.store import _hash_path

    store_dir = tmp_path / ".arachna" / "store"
    obj_path = _hash_path(store_dir, obj_hash)
    assert obj_path.stat().st_size < len(data)


def test_write_object_no_compress_small(tmp_path):
    data = b"hi"
    obj_hash = write_object(data, root=tmp_path)
    from arachna.snapshot.store import _hash_path

    store_dir = tmp_path / ".arachna" / "store"
    obj_path = _hash_path(store_dir, obj_hash)
    assert obj_path.read_bytes() == data


def test_read_object_not_found(tmp_path):
    with pytest.raises(ObjectNotFoundError):
        read_object("abcdef1234567890abcdef1234567890abcdef12", root=tmp_path)


def test_read_object_corrupted(tmp_path):
    obj_hash = write_object(b"original", root=tmp_path)
    from arachna.snapshot.store import _hash_path

    store_dir = tmp_path / ".arachna" / "store"
    obj_path = _hash_path(store_dir, obj_hash)
    obj_path.write_bytes(b"tampered content")
    with pytest.raises(CorruptedStoreError):
        read_object(obj_hash, root=tmp_path)


def test_create_and_load_snapshot(tmp_path):
    files = {"src/main.py": "print('hello')", "README.md": "# Project"}
    sid = create_snapshot(files, profile="code", name="test-snap", root=tmp_path)
    manifest = load_snapshot(sid, root=tmp_path)
    assert manifest["id"] == "test-snap"
    assert manifest["name"] == "test-snap"
    assert manifest["profile"] == "code"
    assert len(manifest["files"]) == 2
    assert "src/main.py" in manifest["files"]
    assert manifest["files"]["src/main.py"].startswith("sha256:")


def test_create_snapshot_updates_head(tmp_path):
    sid = create_snapshot({"a.py": "x"}, name="head-test", root=tmp_path)
    head = (tmp_path / ".arachna" / "store" / "HEAD").read_text().strip()
    assert head == sid


def test_list_snapshots(tmp_path):
    create_snapshot({"a.py": "1"}, name="snap-a", root=tmp_path)
    create_snapshot({"b.py": "2"}, name="snap-b", root=tmp_path)
    snaps = list_snapshots(root=tmp_path)
    assert len(snaps) == 2
    ids = [s["id"] for s in snaps]
    assert "snap-b" in ids
    assert "snap-a" in ids


def test_delete_snapshot(tmp_path):
    sid = create_snapshot({"a.py": "x"}, name="to-delete", root=tmp_path)
    obj_hash = load_snapshot(sid, root=tmp_path)["files"]["a.py"][7:]
    delete_snapshot(sid, root=tmp_path)
    with pytest.raises(ObjectNotFoundError):
        load_snapshot(sid, root=tmp_path)
    result = read_object(obj_hash, root=tmp_path)
    assert result == b"x"


def test_delete_snapshot_updates_head(tmp_path):
    sid1 = create_snapshot({"a.py": "1"}, name="first", root=tmp_path)
    sid2 = create_snapshot({"b.py": "2"}, name="second", root=tmp_path)
    delete_snapshot(sid2, root=tmp_path)
    head = (tmp_path / ".arachna" / "store" / "HEAD").read_text().strip()
    assert head == sid1
    delete_snapshot(sid1, root=tmp_path)
    head_path = tmp_path / ".arachna" / "store" / "HEAD"
    assert not head_path.exists()


def test_delete_snapshot_not_found(tmp_path):
    with pytest.raises(ObjectNotFoundError):
        delete_snapshot("nonexistent", root=tmp_path)


def test_gc_removes_unreferenced_objects(tmp_path):
    orphan_hash = write_object(b"orphan data", root=tmp_path)
    sid = create_snapshot({"a.py": "hello"}, name="gc-test", root=tmp_path)
    snapshot_hash = load_snapshot(sid, root=tmp_path)["files"]["a.py"][7:]
    result = gc(root=tmp_path)
    assert result["removed"] >= 1
    with pytest.raises(ObjectNotFoundError):
        read_object(orphan_hash, root=tmp_path)
    assert read_object(snapshot_hash, root=tmp_path) == b"hello"


def test_gc_empty_store(tmp_path):
    result = gc(root=tmp_path)
    assert result == {"removed": 0, "freed_bytes": 0}


def test_stats(tmp_path):
    create_snapshot({"a.py": "first file"}, name="snap1", root=tmp_path)
    create_snapshot({"a.py": "first file", "b.py": "second file"}, name="snap2", root=tmp_path)
    s = stats(root=tmp_path)
    assert s["snapshots"] == 2
    assert s["objects"] >= 2
    assert s["total_bytes"] > 0
    assert s["unique_bytes"] > 0
    assert 0 <= s["dedup_pct"] <= 100


def test_stats_empty_store(tmp_path):
    s = stats(root=tmp_path)
    assert s == {
        "snapshots": 0,
        "objects": 0,
        "total_bytes": 0,
        "unique_bytes": 0,
        "dedup_pct": 0.0,
    }


def test_arachna_gitignore_created(tmp_path):
    write_object(b"hello", root=tmp_path)
    gitignore = tmp_path / ".arachna" / ".gitignore"
    assert gitignore.exists()
    assert "*" in gitignore.read_text()


def test_load_snapshot_not_found(tmp_path):
    with pytest.raises(ObjectNotFoundError):
        load_snapshot("nonexistent", root=tmp_path)
