# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Content-addressable store for Watch snapshots.

Storage layout under .arachna/ (created lazily on first write):

    .arachna/
      .gitignore          # "*" — never commit this directory
      store/
        objects/
          ab/cd1234...    # zlib-compressed file content (atomic write)
        snapshots/
          20260603T103000.json   # manifest
        HEAD                     # text file with latest snapshot ID

Objects are stored by SHA256 hash. Atomic writes via tempfile + os.replace.
Snapshots are NOT atomic: objects are written first, then manifest.
If process crashes between object write and manifest write, orphan objects
remain — gc() cleans them up.
"""

import contextlib
import hashlib
import json
import logging
import os
import re
import tempfile
import zlib
from datetime import datetime
from pathlib import Path

from .store_errors import CorruptedStoreError, ObjectNotFoundError, SnapshotExistsError

logger = logging.getLogger("arachna.store")

_SNAPSHOT_ID_RE = re.compile(r"^[\w][\w.-]*$")


def validate_snapshot_id(sid: str) -> None:
    if not sid or not _SNAPSHOT_ID_RE.match(sid):
        raise ValueError(
            f"Invalid snapshot ID: '{sid}'. Must match pattern: letters, digits, underscore, dot, hyphen. Cannot be empty or contain path separators."
        )


def _store_root(root: Path | None = None) -> Path:
    if root is None:
        root = Path.cwd()
    arachna_dir = root / ".arachna"
    gitignore = arachna_dir / ".gitignore"
    if not arachna_dir.is_dir():
        arachna_dir.mkdir(parents=True, exist_ok=True)
        try:
            fd, tmp = tempfile.mkstemp(dir=str(arachna_dir), prefix=".gitignore_", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write("*\n")
                os.replace(tmp, gitignore)
            except Exception:
                with contextlib.suppress(OSError):
                    os.unlink(tmp)
                raise
        except OSError:
            gitignore.write_text("*\n")
    store_dir = arachna_dir / "store"
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir


def _hash_path(store_dir: Path, object_hash: str, mkdir: bool = False) -> Path:
    objects_dir = store_dir / "objects"
    prefix = object_hash[:2]
    rest = object_hash[2:]
    obj_dir = objects_dir / prefix
    if mkdir:
        obj_dir.mkdir(parents=True, exist_ok=True)
    return obj_dir / rest


def write_object(data: bytes, root: Path | None = None) -> str:
    """Write an object to the store.

    Atomicity is best-effort: tries tempfile + os.replace first.
    Falls back to direct write if mkstemp fails (e.g. permissions, disk full).
    Crash during fallback may corrupt the object file.
    """
    object_hash = hashlib.sha256(data).hexdigest()
    store_dir = _store_root(root)
    path = _hash_path(store_dir, object_hash, mkdir=True)
    if path.exists():
        return object_hash
    compressed = zlib.compress(data)
    content = compressed if len(compressed) < len(data) else data
    try:
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".obj_", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(content)
            os.replace(tmp, path)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise
    except OSError:
        path.write_bytes(content)
    return object_hash


def read_object(object_hash: str, root: Path | None = None) -> bytes:
    store_dir = _store_root(root)
    path = _hash_path(store_dir, object_hash, mkdir=False)
    if not path.exists():
        raise ObjectNotFoundError(f"Object not found: {object_hash}")
    raw = path.read_bytes()
    try:
        data = zlib.decompress(raw)
    except zlib.error:
        data = raw
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != object_hash:
        raise CorruptedStoreError(
            f"Object {object_hash} is corrupted: expected hash {object_hash}, got {actual_hash}."
        )
    return data


def create_snapshot(
    files: dict[str, str],
    profile_dict: dict | None = None,
    profile: str = "full",
    name: str | None = None,
    pre_commands: dict[str, str] | None = None,
    command: dict[str, str] | None = None,
    root: Path | None = None,
) -> str:
    """Create a snapshot. Not atomic — objects written first, then manifest.

    If process crashes between object writes and manifest write, orphan
    objects remain in store/. Run gc() to clean them up.
    """
    if name is not None:
        validate_snapshot_id(name)
    store_dir = _store_root(root)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_id = name if name else datetime.now().strftime("%Y%m%dT%H%M%S")
    manifest_path = snapshots_dir / f"{snapshot_id}.json"
    if name and manifest_path.exists():
        raise SnapshotExistsError(f"Snapshot '{name}' already exists.")
    file_hashes = {}
    for path, content in files.items():
        obj_hash = write_object(content.encode("utf-8"), root=root)
        file_hashes[path] = f"sha256:{obj_hash}"
    manifest = {
        "id": snapshot_id,
        "name": name,
        "created": datetime.now().isoformat(),
        "profile": profile_dict if profile_dict else profile,
        "files": file_hashes,
    }
    if pre_commands:
        manifest["pre_commands"] = pre_commands
    if command:
        manifest["command"] = command
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    head_path = store_dir / "HEAD"
    head_path.write_text(snapshot_id + "\n")
    return snapshot_id


def update_snapshot(
    snapshot_id: str,
    files: dict[str, str],
    profile_dict: dict | None = None,
    pre_commands: dict[str, str] | None = None,
    command: dict[str, str] | None = None,
    root: Path | None = None,
) -> str:
    validate_snapshot_id(snapshot_id)
    manifest = load_snapshot(snapshot_id, root=root)
    file_hashes = {}
    for path, content in files.items():
        obj_hash = write_object(content.encode("utf-8"), root=root)
        file_hashes[path] = f"sha256:{obj_hash}"
    manifest["files"] = file_hashes
    manifest["created"] = datetime.now().isoformat()
    if profile_dict is not None:
        manifest["profile"] = profile_dict
    if pre_commands is not None:
        manifest["pre_commands"] = pre_commands
    elif "pre_commands" in manifest:
        del manifest["pre_commands"]
    if command is not None:
        manifest["command"] = command
    elif "command" in manifest:
        del manifest["command"]
    store_dir = _store_root(root)
    manifest_path = store_dir / "snapshots" / f"{snapshot_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    head_path = store_dir / "HEAD"
    if head_path.exists() and head_path.read_text().strip() == snapshot_id:
        head_path.write_text(snapshot_id + "\n")
    return snapshot_id


def load_snapshot(snapshot_id: str, root: Path | None = None) -> dict:
    validate_snapshot_id(snapshot_id)
    store_dir = _store_root(root)
    manifest_path = store_dir / "snapshots" / f"{snapshot_id}.json"
    if not manifest_path.exists():
        raise ObjectNotFoundError(f"Snapshot not found: {snapshot_id}")
    return json.loads(manifest_path.read_text())


def list_snapshots(root: Path | None = None) -> list[dict]:
    store_dir = _store_root(root)
    snapshots_dir = store_dir / "snapshots"
    if not snapshots_dir.is_dir():
        return []
    manifests = []
    for mf in sorted(snapshots_dir.glob("*.json"), reverse=True):
        try:
            manifests.append(json.loads(mf.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    manifests.sort(key=lambda m: m.get("created", ""), reverse=True)
    return manifests


def _load_all_manifests(store_dir: Path) -> list[dict]:
    snapshots_dir = store_dir / "snapshots"
    if not snapshots_dir.is_dir():
        return []
    manifests = []
    for mf in sorted(snapshots_dir.glob("*.json")):
        try:
            manifests.append(json.loads(mf.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return manifests


def _collect_referenced_hashes(manifests: list[dict]) -> set[str]:
    referenced: set[str] = set()
    for manifest in manifests:
        for hash_spec in manifest.get("files", {}).values():
            if hash_spec.startswith("sha256:"):
                referenced.add(hash_spec[7:])
        for hash_spec in manifest.get("pre_commands", {}).values():
            if hash_spec.startswith("sha256:"):
                referenced.add(hash_spec[7:])
        for hash_spec in manifest.get("command", {}).values():
            if hash_spec.startswith("sha256:"):
                referenced.add(hash_spec[7:])
    return referenced


def delete_snapshot(snapshot_id: str, root: Path | None = None) -> None:
    validate_snapshot_id(snapshot_id)
    store_dir = _store_root(root)
    manifest_path = store_dir / "snapshots" / f"{snapshot_id}.json"
    if not manifest_path.exists():
        raise ObjectNotFoundError(f"Snapshot not found: {snapshot_id}")
    manifest_path.unlink()
    head_path = store_dir / "HEAD"
    if head_path.exists() and head_path.read_text().strip() == snapshot_id:
        remaining = list_snapshots(root=root)
        if remaining:
            head_path.write_text(remaining[0]["id"] + "\n")
        else:
            head_path.unlink()


def rename_snapshot(old_id: str, new_id: str, root: Path | None = None) -> str:
    validate_snapshot_id(old_id)
    validate_snapshot_id(new_id)
    store_dir = _store_root(root)
    snapshots_dir = store_dir / "snapshots"
    old_path = snapshots_dir / f"{old_id}.json"
    new_path = snapshots_dir / f"{new_id}.json"
    if not old_path.exists():
        raise ObjectNotFoundError(f"Snapshot not found: {old_id}")
    if new_path.exists():
        raise SnapshotExistsError(f"Snapshot '{new_id}' already exists.")
    manifest = json.loads(old_path.read_text())
    manifest["id"] = new_id
    manifest["name"] = new_id
    new_path.write_text(json.dumps(manifest, indent=2) + "\n")
    old_path.unlink()
    head_path = store_dir / "HEAD"
    if head_path.exists() and head_path.read_text().strip() == old_id:
        head_path.write_text(new_id + "\n")
    return new_id


def gc(root: Path | None = None) -> dict:
    store_dir = _store_root(root)
    objects_dir = store_dir / "objects"
    if not objects_dir.is_dir():
        return {"removed": 0, "freed_bytes": 0}
    manifests = _load_all_manifests(store_dir)
    referenced = _collect_referenced_hashes(manifests)
    removed = 0
    freed_bytes = 0
    for obj_file in objects_dir.rglob("*"):
        if not obj_file.is_file():
            continue
        rel = obj_file.relative_to(objects_dir)
        obj_hash = str(rel).replace(os.sep, "")
        if obj_hash not in referenced:
            with contextlib.suppress(OSError):
                freed_bytes += obj_file.stat().st_size
            obj_file.unlink()
            removed += 1
    for subdir in sorted(objects_dir.glob("*"), reverse=True):
        if subdir.is_dir():
            with contextlib.suppress(OSError):
                subdir.rmdir()
    return {"removed": removed, "freed_bytes": freed_bytes}


def stats(root: Path | None = None) -> dict:
    store_dir = _store_root(root)
    objects_dir = store_dir / "objects"
    manifests = _load_all_manifests(store_dir)
    snapshots_count = len(manifests)
    objects_count = 0
    total_bytes = 0
    if objects_dir.is_dir():
        for obj_file in objects_dir.rglob("*"):
            if obj_file.is_file():
                objects_count += 1
                with contextlib.suppress(OSError):
                    total_bytes += obj_file.stat().st_size
    referenced_hashes = _collect_referenced_hashes(manifests)
    unique_bytes = 0
    for obj_hash in referenced_hashes:
        obj_path = _hash_path(store_dir, obj_hash, mkdir=False)
        if obj_path.exists():
            with contextlib.suppress(OSError):
                unique_bytes += obj_path.stat().st_size
    dedup_pct = 0.0
    if total_bytes > 0:
        dedup_pct = round((1 - unique_bytes / total_bytes) * 100, 1)
    return {
        "snapshots": snapshots_count,
        "objects": objects_count,
        "total_bytes": total_bytes,
        "unique_bytes": unique_bytes,
        "dedup_pct": dedup_pct,
    }
