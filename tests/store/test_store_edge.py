"""Edge case tests for store.py."""

from arachna.store import gc, stats


def test_gc_no_objects_dir(tmp_path):
    """gc returns zeros when objects dir doesn't exist."""
    result = gc(root=tmp_path)
    assert result == {"removed": 0, "freed_bytes": 0}


def test_stats_no_snapshots_dir(tmp_path):
    """stats returns zeros when snapshots dir doesn't exist."""
    s = stats(root=tmp_path)
    assert s["snapshots"] == 0
    assert s["objects"] == 0


def test_stats_no_objects_dir(tmp_path):
    """stats returns zero objects when objects dir doesn't exist."""
    from arachna.store import create_snapshot

    create_snapshot({"a.py": "hello"}, name="s1", root=tmp_path)

    import shutil

    shutil.rmtree(tmp_path / ".arachna" / "store" / "objects")

    s = stats(root=tmp_path)
    assert s["snapshots"] == 1
    assert s["objects"] == 0


def test_list_snapshots_empty_dir(tmp_path):
    """list_snapshots returns empty list when snapshots dir doesn't exist."""
    from arachna.store import list_snapshots

    snaps = list_snapshots(root=tmp_path)
    assert snaps == []


def test_list_snapshots_corrupted_manifest(tmp_path):
    """list_snapshots skips corrupted manifest files."""
    from arachna.store import _store_root

    store_dir = _store_root(tmp_path)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    (snapshots_dir / "corrupted.json").write_text("not json")

    from arachna.store import list_snapshots

    snaps = list_snapshots(root=tmp_path)
    assert isinstance(snaps, list)


def test_delete_snapshot_clears_head(tmp_path):
    """Deleting the only snapshot clears HEAD."""
    from arachna.store import _store_root, create_snapshot, delete_snapshot

    sid = create_snapshot({"a.py": "x"}, name="only-snap", root=tmp_path)
    delete_snapshot(sid, root=tmp_path)

    head_path = _store_root(tmp_path) / "HEAD"
    assert not head_path.exists()


def test_gc_with_corrupted_manifest(tmp_path):
    """gc handles corrupted manifest files gracefully."""
    from arachna.store import _store_root, write_object

    write_object(b"data", root=tmp_path)
    store_dir = _store_root(tmp_path)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    (snapshots_dir / "bad.json").write_text("{invalid")

    result = gc(root=tmp_path)
    assert result["removed"] >= 0


def test_stats_with_corrupted_manifest(tmp_path):
    """stats handles corrupted manifest files gracefully."""
    from arachna.store import _store_root, write_object

    write_object(b"data", root=tmp_path)
    store_dir = _store_root(tmp_path)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    (snapshots_dir / "bad.json").write_text("{invalid")

    s = stats(root=tmp_path)
    assert s["snapshots"] >= 0
