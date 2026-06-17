# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""File modification cache for incremental collection.

Cache format v2:
    {"_version": 2, "files": {"/abs/path/to/file.py": {"mtime_ns": ..., "size": ..., "hash": ...}}}

Smart hybrid algorithm:
1. stat() -> size, mtime_ns
2. If size == cached.size AND abs(mtime_ns - cached.mtime_ns) < 1ms -> FAST PATH, skip.
3. Else -> compute SHA256. If hash matches -> false positive, update mtime_ns, skip.
   If hash differs -> REAL CHANGE, mark as modified.
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
        return hashlib.sha256(filepath.read_bytes()).hexdigest()
    except OSError:
        return None


def load_cache(out_dir: Path) -> dict[str, dict]:
    cf = out_dir / _CACHE_FILE
    if cf.exists():
        with contextlib.suppress(json.JSONDecodeError, OSError):
            data = json.loads(cf.read_text())
            if isinstance(data, dict) and data.get("_version", 1) >= _VERSION:
                return data.get("files", {})
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


def _is_fast_path(size, mtime_ns, entry):
    cached_size = entry.get("size")
    cached_mtime_ns = entry.get("mtime_ns")
    return (
        cached_size is not None
        and cached_mtime_ns is not None
        and size == cached_size
        and abs(mtime_ns - cached_mtime_ns) < _MTIME_NS_TOLERANCE
    )


def _is_false_positive(fp, mtime_ns, entry):
    old_hash = entry.get("hash")
    new_hash = _file_hash(fp)
    if new_hash is not None and old_hash is not None and new_hash == old_hash:
        entry["mtime_ns"] = mtime_ns
        return True
    return False


def _check_file(fp, cache):
    key = str(fp)
    if key not in cache:
        return "new"
    try:
        st = fp.stat()
    except OSError:
        return "skip"
    size = st.st_size
    mtime_ns = st.st_mtime_ns
    if _is_fast_path(size, mtime_ns, cache[key]):
        return "unchanged"
    if _is_false_positive(fp, mtime_ns, cache[key]):
        return "unchanged"
    return "changed"


def get_changed_files(
    filepaths: list[Path], cache: dict[str, dict]
) -> tuple[list[Path], list[Path], list[Path]]:
    changed = []
    new = []
    seen = set()
    for fp in filepaths:
        key = str(fp)
        seen.add(key)
        if not fp.exists():
            continue
        result = _check_file(fp, cache)
        if result == "new":
            new.append(fp)
        elif result == "changed":
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
