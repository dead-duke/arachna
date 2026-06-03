import time
from pathlib import Path

from arachna.cache import get_changed_files, load_cache, save_cache, update_cache


def _make_entry(filepath: Path) -> dict:
    """Create a cache entry for a file with real mtime_ns, size, and hash."""
    import hashlib

    st = filepath.stat()
    return {
        "mtime_ns": st.st_mtime_ns,
        "size": st.st_size,
        "hash": hashlib.sha256(filepath.read_bytes()).hexdigest(),
    }


def test_load_cache_empty(tmp_path):
    cache = load_cache(tmp_path)
    assert cache == {}


def test_save_and_load_cache(tmp_path):
    entry = {"mtime_ns": 1734567890123456789, "size": 100, "hash": "abc"}
    save_cache(tmp_path, {"a.py": entry})
    cache = load_cache(tmp_path)
    assert cache == {"a.py": entry}


def test_save_cache_includes_version(tmp_path):
    """save_cache writes _version field in payload."""
    import json

    save_cache(tmp_path, {})
    data = json.loads((tmp_path / ".arachna_cache.json").read_text())
    assert data["_version"] == 2
    assert data["files"] == {}


def test_get_changed_files_all_new(tmp_path):
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    a.write_text("hello")
    b.write_text("world")
    cache = {}

    changed, new, deleted = get_changed_files([a, b], cache)
    assert len(changed) == 0
    assert len(new) == 2
    assert len(deleted) == 0


def test_get_changed_files_none_changed(tmp_path):
    """Fast path: size and mtime_ns match — file skipped."""
    a = tmp_path / "a.py"
    a.write_text("hello")
    cache = {str(a): _make_entry(a)}

    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0
    assert len(new) == 0
    assert len(deleted) == 0


def test_get_changed_files_modified(tmp_path):
    """Real modification: size changes, hash changes — marked as changed."""
    a = tmp_path / "a.py"
    a.write_text("original")
    cache = {str(a): _make_entry(a)}
    time.sleep(0.01)
    a.write_text("modified")

    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1
    assert len(new) == 0
    assert len(deleted) == 0


def test_get_changed_files_deleted(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    cache = {str(a): _make_entry(a)}
    a.unlink()

    changed, new, deleted = get_changed_files([], cache)
    assert len(changed) == 0
    assert len(new) == 0
    assert len(deleted) == 1


def test_get_changed_files_mixed(tmp_path):
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    c = tmp_path / "c.py"
    a.write_text("unchanged")
    b.write_text("original")
    cache = {str(a): _make_entry(a), str(b): _make_entry(b)}
    time.sleep(0.01)
    b.write_text("modified")
    c.write_text("new file")

    changed, new, deleted = get_changed_files([a, b, c], cache)
    assert len(changed) == 1
    assert str(b) in [str(x) for x in changed]
    assert len(new) == 1
    assert str(c) in [str(x) for x in new]
    assert len(deleted) == 0


def test_update_cache(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("hello")
    cache = {}
    updated = update_cache([a], cache)
    assert str(a) in updated
    entry = updated[str(a)]
    assert "mtime_ns" in entry
    assert entry["mtime_ns"] == a.stat().st_mtime_ns
    assert "size" in entry
    assert entry["size"] == a.stat().st_size
    assert "hash" in entry
    assert isinstance(entry["hash"], str)


def test_update_cache_nonexistent_file(tmp_path):
    """update_cache skips files that don't exist."""
    a = tmp_path / "ghost.py"
    cache = {}
    updated = update_cache([a], cache)
    assert str(a) not in updated


def test_get_changed_files_large_file(tmp_path):
    """Files with mtime change and None hash are treated as changed."""
    a = tmp_path / "big.py"
    a.write_text("hello")
    cache = {str(a): {"mtime_ns": 0, "size": a.stat().st_size, "hash": None}}
    time.sleep(0.01)
    a.write_text("modified big")

    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1
    assert len(new) == 0


def test_get_changed_files_missing_from_disk(tmp_path):
    """Files in filepaths list that don't exist are skipped."""
    a = tmp_path / "ghost.py"
    cache = {}
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0
    assert len(new) == 0
    assert len(deleted) == 0


def test_save_cache_fallback(tmp_path, monkeypatch):
    """save_cache falls back to direct write when tempfile fails."""
    import arachna.cache as cache_module

    def failing_mkstemp(*args, **kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(cache_module.tempfile, "mkstemp", failing_mkstemp)
    save_cache(tmp_path, {"a.py": {"mtime_ns": 1, "size": 100, "hash": "abc"}})

    assert (tmp_path / ".arachna_cache.json").exists()


# ── v1.5.3 smart hybrid tests ──────────────────────────────────────


def test_mtime_ns_unchanged_skipped(tmp_path):
    """Fast path: same size + mtime_ns within tolerance → file skipped."""
    a = tmp_path / "a.py"
    a.write_text("hello")
    cache = {str(a): _make_entry(a)}

    # File not modified — stat should be identical
    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0
    assert len(new) == 0


def test_mtime_ns_false_positive(tmp_path):
    """git checkout scenario: mtime changes but content same → false positive,
    mtime_ns updated, NOT marked as changed."""
    a = tmp_path / "a.py"
    a.write_text("unchanged content")
    cache = {str(a): _make_entry(a)}

    # Simulate git checkout: force mtime change but same content
    old_mtime_ns = cache[str(a)]["mtime_ns"]
    # Touch the file to bump mtime
    time.sleep(0.01)
    a.write_text("unchanged content")  # same content, new mtime

    changed, new, deleted = get_changed_files([a], cache)
    # Content unchanged — should NOT be marked as changed
    assert len(changed) == 0, f"Expected 0 changed, got {changed}"
    # Cache should have updated mtime_ns
    assert cache[str(a)]["mtime_ns"] > old_mtime_ns


def test_size_changed_real_modification(tmp_path):
    """Size differs AND hash differs → real modification, marked as changed."""
    a = tmp_path / "a.py"
    a.write_text("short")
    cache = {str(a): _make_entry(a)}
    time.sleep(0.01)
    a.write_text("much longer content now")

    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1


def test_mtime_ns_within_tolerance(tmp_path):
    """mtime_ns difference < 1ms → treated as unchanged (fast path)."""
    a = tmp_path / "a.py"
    a.write_text("hello")
    st = a.stat()
    # Cache entry with mtime_ns 100ns different — within 1ms tolerance
    cache = {
        str(a): {
            "mtime_ns": st.st_mtime_ns - 100,
            "size": st.st_size,
            "hash": _make_entry(a)["hash"],
        }
    }

    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0


def test_mtime_ns_exceeds_tolerance(tmp_path):
    """mtime_ns difference >= 1ms → triggers SHA256 check."""
    a = tmp_path / "a.py"
    a.write_text("hello")
    st = a.stat()
    # Cache entry with mtime_ns 2ms different — exceeds tolerance
    cache = {
        str(a): {
            "mtime_ns": st.st_mtime_ns - 2_000_000,
            "size": st.st_size,
            "hash": _make_entry(a)["hash"],
        }
    }

    changed, new, deleted = get_changed_files([a], cache)
    # Same content → hash matches → false positive, NOT changed
    assert len(changed) == 0


def test_cache_migration_old_format(tmp_path):
    """Old v1 format ({mtime, hash}) is detected and invalidated."""
    import json

    a = tmp_path / "a.py"
    a.write_text("hello")

    # Write old-format cache (v1 — no _version, no mtime_ns)
    old_cache = {str(a): {"mtime": 1.0, "hash": "abc"}}
    (tmp_path / ".arachna_cache.json").write_text(json.dumps(old_cache))

    # load_cache should detect old format and return empty
    cache = load_cache(tmp_path)
    assert cache == {}, f"Expected empty cache after migration, got {cache}"


def test_mtime_ns_none_hash(tmp_path):
    """Large file with None hash in cache — always treated as changed."""
    a = tmp_path / "big.py"
    a.write_text("hello")
    cache = {str(a): {"mtime_ns": 0, "size": a.stat().st_size, "hash": None}}
    time.sleep(0.01)
    a.write_text("modified")

    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1
