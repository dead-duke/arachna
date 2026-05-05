"""File modification time cache for incremental collection."""

import json
from pathlib import Path

_CACHE_FILE = ".arachna_cache.json"


def load_cache(out_dir: Path) -> dict[str, float]:
    """Load {filepath: mtime} cache."""
    cf = out_dir / _CACHE_FILE
    if cf.exists():
        try:
            return json.loads(cf.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_cache(out_dir: Path, cache: dict[str, float]):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / _CACHE_FILE).write_text(json.dumps(cache, indent=2))


def get_changed_files(
    filepaths: list[Path],
    cache: dict[str, float],
) -> tuple[list[Path], list[Path], list[Path]]:
    """Compare files against cache.

    Returns (changed, new, deleted) lists.
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
        elif mtime != cache[key]:
            changed.append(fp)

    deleted = [Path(k) for k in cache if k not in seen]

    return changed, new, deleted


def update_cache(filepaths: list[Path], cache: dict[str, float]) -> dict[str, float]:
    """Update cache with current mtimes."""
    for fp in filepaths:
        if fp.exists():
            cache[str(fp)] = fp.stat().st_mtime
    return cache
