"""File modification cache for incremental collection.

Cache format v2:
    {
        "_version": 2,
        "files": {
            "/abs/path/to/file.py": {
                "mtime_ns": 1734567890123456789,
                "size": 12345,
                "hash": "abc123..."
            }
        }
    }

Smart hybrid algorithm:
1. stat() → size, mtime_ns
2. If size == cached.size AND abs(mtime_ns - cached.mtime_ns) < 1ms:
   FAST PATH — file unchanged, skip. (99% of cases)
3. Else — compute SHA256.
   If hash == cached.hash:
       FALSE POSITIVE (git checkout, touch, etc.) — update mtime_ns, skip.
   If hash != cached.hash:
       REAL CHANGE — mark as modified.

NOTE: get_changed_files mutates the cache dict to update mtime_ns
for false positives. Callers must save the mutated cache after use.
"""

import contextlib
import hashlib
import json
import os
import tempfile
from pathlib import Path

_CACHE_FILE = ".arachna_cache.json"
_VERSION = 2
_MAX_HASH_SIZE = int(os.environ.get("ARACHNA_MAX_HASH_SIZE", 10 * 1024 * 1024))
_MTIME_NS_TOLERANCE = 1_000_000


def _file_hash(filepath: Path) -> str | None:
    try:
        if filepath.stat().st_size > _MAX_HASH_SIZE:
            return None
        content = filepath.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except OSError:
        return None


def load_cache(out_dir: Path) -> dict[str, dict]:
    cf = out_dir / _CACHE_FILE
    if cf.exists():
        with contextlib.suppress(json.JSONDecodeError, OSError):
            data = json.loads(cf.read_text())
            if isinstance(data, dict):
                version = data.get("_version", 1)
                files = data.get("files", {})
                if version < _VERSION:
                    return {}
                return files
    return {}


def save_cache(out_dir: Path, cache: dict[str, dict]):
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = out_dir / _CACHE_FILE
    payload = {"_version": _VERSION, "files": cache}
    try:
        fd, tmp_path = tempfile.mkstemp(dir=str(out_dir), prefix=".arachna_cache_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp_path, cache_path)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise
    except OSError:
        cache_path.write_text(json.dumps(payload, indent=2))


def get_changed_files(
    filepaths: list[Path],
    cache: dict[str, dict],
) -> tuple[list[Path], list[Path], list[Path]]:
    """Compare files against cache using smart hybrid algorithm.

    Returns (changed, new, deleted) lists.
    Mutates cache dict to update mtime_ns for false positives.
    Callers must save the mutated cache after use.
    """
    changed = []
    new = []
    seen = set()

    for fp in filepaths:
        key = str(fp)
        seen.add(key)
        if not fp.exists():
            continue
        try:
            st = fp.stat()
        except OSError:
            continue

        size = st.st_size
        mtime_ns = st.st_mtime_ns

        if key not in cache:
            new.append(fp)
            continue

        entry = cache[key]
        cached_size = entry.get("size")
        cached_mtime_ns = entry.get("mtime_ns")

        if (
            cached_size is not None
            and cached_mtime_ns is not None
            and size == cached_size
            and abs(mtime_ns - cached_mtime_ns) < _MTIME_NS_TOLERANCE
        ):
            continue

        old_hash = entry.get("hash")
        new_hash = _file_hash(fp)

        if new_hash is not None and old_hash is not None and new_hash == old_hash:
            cache[key]["mtime_ns"] = mtime_ns
            continue

        changed.append(fp)

    deleted = [Path(k) for k in cache if k not in seen]
    return changed, new, deleted


def update_cache(filepaths: list[Path], cache: dict[str, dict]) -> dict[str, dict]:
    for fp in filepaths:
        if fp.exists():
            try:
                st = fp.stat()
            except OSError:
                continue
            cache[str(fp)] = {
                "mtime_ns": st.st_mtime_ns,
                "size": st.st_size,
                "hash": _file_hash(fp),
            }
    return cache
