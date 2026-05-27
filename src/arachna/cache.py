"""File modification cache for incremental collection."""

import contextlib
import hashlib
import json
import os
import tempfile
from pathlib import Path

_CACHE_FILE = ".arachna_cache.json"

# Max file size for hashing (10 MB)
_MAX_HASH_SIZE = 10 * 1024 * 1024


def _file_hash(filepath: Path) -> str | None:
    """Compute SHA256 hash of file contents.

    Returns None for files > _MAX_HASH_SIZE or unreadable files.
    """
    try:
        if filepath.stat().st_size > _MAX_HASH_SIZE:
            return None
        content = filepath.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except OSError:
        return None


def load_cache(out_dir: Path) -> dict[str, dict]:
    """Load {filepath: {mtime, hash}} cache."""
    cf = out_dir / _CACHE_FILE
    if cf.exists():
        with contextlib.suppress(json.JSONDecodeError, OSError):
            return json.loads(cf.read_text())
    return {}


def save_cache(out_dir: Path, cache: dict[str, dict]):
    """Atomically write cache to disk."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = out_dir / _CACHE_FILE
    try:
        fd, tmp_path = tempfile.mkstemp(dir=str(out_dir), prefix=".arachna_cache_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
            os.replace(tmp_path, cache_path)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise
    except OSError:
        # Fallback: direct write
        cache_path.write_text(json.dumps(cache, indent=2))


def get_changed_files(
    filepaths: list[Path],
    cache: dict[str, dict],
) -> tuple[list[Path], list[Path], list[Path]]:
    """Compare files against cache using mtime + content hash.

    Returns (changed, new, deleted) lists.
    Changed = mtime differs AND hash differs (real content change).
    """
    changed = []
    new = []
    seen = set()

    for fp in filepaths:
        key = str(fp)
        seen.add(key)
        if not fp.exists():
            continue
        mtime = fp.stat().st_mtime
        if key not in cache:
            new.append(fp)
        elif mtime != cache[key]["mtime"]:
            # mtime changed — verify content actually changed
            old_hash = cache[key].get("hash")
            new_hash = _file_hash(fp)
            if new_hash is not None and old_hash is not None and new_hash != old_hash:
                changed.append(fp)
            elif new_hash is None or old_hash is None:
                # Can't compare hashes — trust mtime
                changed.append(fp)

    deleted = [Path(k) for k in cache if k not in seen]

    return changed, new, deleted


def update_cache(filepaths: list[Path], cache: dict[str, dict]) -> dict[str, dict]:
    """Update cache with current mtimes and content hashes."""
    for fp in filepaths:
        if fp.exists():
            cache[str(fp)] = {
                "mtime": fp.stat().st_mtime,
                "hash": _file_hash(fp),
            }
    return cache
