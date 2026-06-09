"""Explicit test for SHA256 fallback path in cache (v2.9.2)."""

from arachna.cache import get_changed_files


def test_mtime_tolerance_size_differs_hash_same(tmp_path):
    """mtime within tolerance, size differs, hash same → false positive, not changed."""
    a = tmp_path / "a.py"
    a.write_text("hello")

    import hashlib

    st = a.stat()
    # Cache with different size, same content hash, mtime within tolerance
    cache = {
        str(a): {
            "mtime_ns": st.st_mtime_ns,
            "size": 999,
            "hash": hashlib.sha256(b"hello").hexdigest(),
        }
    }

    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 0


def test_mtime_tolerance_size_differs_hash_differs(tmp_path):
    """mtime within tolerance, size differs, hash differs → changed."""
    a = tmp_path / "a.py"
    a.write_text("hello")

    st = a.stat()
    cache = {
        str(a): {
            "mtime_ns": st.st_mtime_ns,
            "size": 999,
            "hash": "different_hash",
        }
    }

    changed, new, deleted = get_changed_files([a], cache)
    assert len(changed) == 1
