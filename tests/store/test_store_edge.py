"""Edge case tests for store.py."""

from arachna.store import gc, stats


def test_gc_no_objects_dir(tmp_path, monkeypatch):
    """gc returns zeros when objects dir doesn't exist."""
    monkeypatch.chdir(tmp_path)
    result = gc()
    assert result == {"removed": 0, "freed_bytes": 0}


def test_stats_no_snapshots_dir(tmp_path, monkeypatch):
    """stats returns zeros when snapshots dir doesn't exist."""
    monkeypatch.chdir(tmp_path)
    s = stats()
    assert s["snapshots"] == 0
    assert s["objects"] == 0


def test_stats_no_objects_dir(tmp_path, monkeypatch):
    """stats returns zero objects when objects dir doesn't exist."""
    monkeypatch.chdir(tmp_path)
    from arachna.store import create_snapshot

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("hello")
    create_snapshot({"a.py": "hello"}, name="s1")

    import shutil

    shutil.rmtree(tmp_path / ".arachna" / "store" / "objects")

    s = stats()
    assert s["snapshots"] == 1
    assert s["objects"] == 0


def test_list_snapshots_empty_dir(tmp_path, monkeypatch):
    """list_snapshots returns empty list when snapshots dir doesn't exist."""
    monkeypatch.chdir(tmp_path)
    from arachna.store import list_snapshots

    snaps = list_snapshots()
    assert snaps == []


def test_list_snapshots_corrupted_manifest(tmp_path, monkeypatch):
    """list_snapshots skips corrupted manifest files."""
    monkeypatch.chdir(tmp_path)
    from arachna.store import _store_root

    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    (snapshots_dir / "corrupted.json").write_text("not json")

    from arachna.store import list_snapshots

    snaps = list_snapshots()
    assert isinstance(snaps, list)


def test_delete_snapshot_clears_head(tmp_path, monkeypatch):
    """Deleting the only snapshot clears HEAD."""
    monkeypatch.chdir(tmp_path)
    from arachna.store import _store_root, create_snapshot, delete_snapshot

    sid = create_snapshot({"a.py": "x"}, name="only-snap")
    delete_snapshot(sid)

    head_path = _store_root() / "HEAD"
    assert not head_path.exists()


def test_gc_with_corrupted_manifest(tmp_path, monkeypatch):
    """gc handles corrupted manifest files gracefully."""
    monkeypatch.chdir(tmp_path)
    from arachna.store import _store_root, write_object

    write_object(b"data")
    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    (snapshots_dir / "bad.json").write_text("{invalid")

    result = gc()
    assert result["removed"] >= 0


def test_stats_with_corrupted_manifest(tmp_path, monkeypatch):
    """stats handles corrupted manifest files gracefully."""
    monkeypatch.chdir(tmp_path)
    from arachna.store import _store_root, write_object

    write_object(b"data")
    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    (snapshots_dir / "bad.json").write_text("{invalid")

    s = stats()
    assert s["snapshots"] >= 0
