import tempfile
from pathlib import Path

from arachna.cache import get_changed_files, load_cache, save_cache, update_cache


def _make_entry(filepath: Path) -> dict:
    """Create a cache entry for a file in the new format."""
    return {
        "mtime": filepath.stat().st_mtime,
        "hash": "dummy",
    }


def test_load_cache_empty():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d)
        cache = load_cache(out)
        assert cache == {}


def test_save_and_load_cache():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d)
        save_cache(out, {"a.py": {"mtime": 1.0, "hash": "abc"}})
        cache = load_cache(out)
        assert cache == {"a.py": {"mtime": 1.0, "hash": "abc"}}


def test_get_changed_files_all_new():
    with tempfile.TemporaryDirectory() as d:
        a = Path(d) / "a.py"
        b = Path(d) / "b.py"
        a.write_text("hello")
        b.write_text("world")
        cache = {}

        changed, new, deleted = get_changed_files([a, b], cache)
        assert len(changed) == 0
        assert len(new) == 2
        assert len(deleted) == 0


def test_get_changed_files_none_changed():
    with tempfile.TemporaryDirectory() as d:
        a = Path(d) / "a.py"
        a.write_text("hello")
        cache = {str(a): _make_entry(a)}

        changed, new, deleted = get_changed_files([a], cache)
        assert len(changed) == 0
        assert len(new) == 0
        assert len(deleted) == 0


def test_get_changed_files_modified():
    with tempfile.TemporaryDirectory() as d:
        a = Path(d) / "a.py"
        a.write_text("original")
        cache = {str(a): _make_entry(a)}
        # Modify the file
        a.write_text("modified")

        changed, new, deleted = get_changed_files([a], cache)
        assert len(changed) == 1
        assert len(new) == 0
        assert len(deleted) == 0


def test_get_changed_files_deleted():
    with tempfile.TemporaryDirectory() as d:
        a = Path(d) / "a.py"
        a.write_text("hello")
        cache = {str(a): _make_entry(a)}
        a.unlink()

        changed, new, deleted = get_changed_files([], cache)
        assert len(changed) == 0
        assert len(new) == 0
        assert len(deleted) == 1


def test_get_changed_files_mixed():
    with tempfile.TemporaryDirectory() as d:
        a = Path(d) / "a.py"
        b = Path(d) / "b.py"
        c = Path(d) / "c.py"
        a.write_text("unchanged")
        b.write_text("original")
        cache = {str(a): _make_entry(a), str(b): _make_entry(b)}
        # Modify b, c is new, nothing deleted
        b.write_text("modified")
        c.write_text("new file")

        changed, new, deleted = get_changed_files([a, b, c], cache)
        assert len(changed) == 1
        assert str(b) in [str(x) for x in changed]
        assert len(new) == 1
        assert str(c) in [str(x) for x in new]
        assert len(deleted) == 0


def test_update_cache():
    with tempfile.TemporaryDirectory() as d:
        a = Path(d) / "a.py"
        a.write_text("hello")
        cache = {}
        updated = update_cache([a], cache)
        assert str(a) in updated
        entry = updated[str(a)]
        assert "mtime" in entry
        assert entry["mtime"] == a.stat().st_mtime
        assert "hash" in entry
        assert isinstance(entry["hash"], str)
