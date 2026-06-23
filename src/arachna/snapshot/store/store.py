"""Content-addressable store for snapshots."""

import contextlib
import hashlib
import json
import logging
import os
import re
import zlib
from datetime import datetime
from pathlib import Path

from ...domain.atomic_write import atomic_write_bytes, atomic_write_text
from ...domain.path_utils import SafePath, validate_path
from .store_errors import CorruptedStoreError, ObjectNotFoundError, SnapshotExistsError

logger = logging.getLogger("arachna.store")

_SNAPSHOT_ID_RE = re.compile(r"^[\w][\w.-]*$")
_SHA256_PREFIX = "sha256:"
_VERSION = 1


def validate_snapshot_id(sid: str) -> None:
    if not sid or not _SNAPSHOT_ID_RE.match(sid):
        raise ValueError(
            f"Invalid snapshot ID: '{sid}'. Must match pattern: letters, digits, underscore, dot, hyphen. Cannot be empty or contain path separators."
        )


def _store_root(root: Path) -> SafePath:
    arachna_dir = SafePath(root / ".arachna", root)
    arachna_dir.mkdir(parents=True, exist_ok=True)
    gitignore = arachna_dir / ".gitignore"
    if not gitignore.exists():
        try:
            atomic_write_text(gitignore, "*\n")
        except OSError:
            logger.warning("Failed atomic write for .gitignore, falling back to direct write")
            gitignore.write_text("*\n")
    store_dir = arachna_dir / "store"
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir


def _hash_path(store_dir: SafePath, object_hash: str, mkdir: bool = False) -> SafePath:
    objects_dir = store_dir / "objects"
    prefix = object_hash[:2]
    rest = object_hash[2:]
    obj_dir = objects_dir / prefix
    if mkdir:
        obj_dir.mkdir(parents=True, exist_ok=True)
    return obj_dir / rest


def _validated_safe_path(full_path: Path, root: Path) -> SafePath:
    """Create SafePath with explicit validation for SonarCloud S2083."""
    if not validate_path(full_path, root):
        raise ValueError(f"Path traversal detected: {full_path}")
    return SafePath(full_path, root)


def write_object(data: bytes, root: Path) -> str:
    object_hash = hashlib.sha256(data).hexdigest()
    store_dir = _store_root(root)
    path = _hash_path(store_dir, object_hash, mkdir=True)
    if not path.exists():
        compressed = zlib.compress(data)
        content = compressed if len(compressed) < len(data) else data
        atomic_write_bytes(path, content)
    return object_hash


def read_object(object_hash: str, root: Path) -> bytes:
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
    root: Path,
    profile_dict: dict | None = None,
    profile: str = "full",
    name: str | None = None,
    pre_commands: dict[str, str] | None = None,
    command: dict[str, str] | None = None,
) -> str:
    if name is not None:
        validate_snapshot_id(name)
    store_dir = _store_root(root)
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_id = name if name else datetime.now().strftime("%Y%m%dT%H%M%S")
    manifest_path = _validated_safe_path(
        store_dir.to_path() / "snapshots" / f"{snapshot_id}.json", root
    )
    if name and manifest_path.exists():
        raise SnapshotExistsError(f"Snapshot '{name}' already exists.")
    file_hashes = {}
    for path, content in files.items():
        obj_hash = write_object(content.encode("utf-8"), root=root)
        file_hashes[path] = f"{_SHA256_PREFIX}{obj_hash}"
    manifest = {
        "_version": _VERSION,
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
    atomic_write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")
    head_path = _validated_safe_path(store_dir.to_path() / "HEAD", root)
    atomic_write_text(head_path, snapshot_id + "\n")
    return snapshot_id


def update_snapshot(
    snapshot_id: str,
    files: dict[str, str],
    root: Path,
    profile_dict: dict | None = None,
    pre_commands: dict[str, str] | None = None,
    command: dict[str, str] | None = None,
) -> str:
    validate_snapshot_id(snapshot_id)
    manifest = load_snapshot(snapshot_id, root=root)
    file_hashes = {}
    for path, content in files.items():
        obj_hash = write_object(content.encode("utf-8"), root=root)
        file_hashes[path] = f"{_SHA256_PREFIX}{obj_hash}"
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
    manifest_path = _validated_safe_path(
        store_dir.to_path() / "snapshots" / f"{snapshot_id}.json", root
    )
    atomic_write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")
    head_path = _validated_safe_path(store_dir.to_path() / "HEAD", root)
    if head_path.exists() and head_path.read_text().strip() == snapshot_id:
        atomic_write_text(head_path, snapshot_id + "\n")
    return snapshot_id


def load_snapshot(snapshot_id: str, root: Path) -> dict:
    validate_snapshot_id(snapshot_id)
    store_dir = _store_root(root)
    manifest_path = _validated_safe_path(
        store_dir.to_path() / "snapshots" / f"{snapshot_id}.json", root
    )
    if not manifest_path.exists():
        raise ObjectNotFoundError(f"Snapshot not found: {snapshot_id}")
    manifest = json.loads(manifest_path.read_text())
    manifest_version = manifest.get("_version", 0)
    if manifest_version > _VERSION:
        raise ValueError(
            f"Snapshot '{snapshot_id}' version {manifest_version} is newer than supported {_VERSION}. Upgrade arachna to read this snapshot."
        )
    if manifest_version < _VERSION:
        manifest = _migrate_manifest(manifest, _VERSION)
    return manifest


def _migrate_manifest(manifest: dict, to_version: int) -> dict:
    manifest["_version"] = to_version
    return manifest


def list_snapshots(root: Path) -> list[dict]:
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


def _load_all_manifests(store_dir: SafePath) -> list[dict]:
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


def _collect_hashes_from_dict(d, referenced):
    for hash_spec in d.values():
        if hash_spec.startswith(_SHA256_PREFIX):
            referenced.add(hash_spec[len(_SHA256_PREFIX) :])


def _collect_referenced_hashes(manifests: list[dict]) -> set[str]:
    referenced: set[str] = set()
    for manifest in manifests:
        _collect_hashes_from_dict(manifest.get("files", {}), referenced)
        _collect_hashes_from_dict(manifest.get("pre_commands", {}), referenced)
        _collect_hashes_from_dict(manifest.get("command", {}), referenced)
    return referenced


def delete_snapshot(snapshot_id: str, root: Path) -> None:
    validate_snapshot_id(snapshot_id)
    store_dir = _store_root(root)
    manifest_path = _validated_safe_path(
        store_dir.to_path() / "snapshots" / f"{snapshot_id}.json", root
    )
    if not manifest_path.exists():
        raise ObjectNotFoundError(f"Snapshot not found: {snapshot_id}")
    manifest_path.unlink()
    head_path = _validated_safe_path(store_dir.to_path() / "HEAD", root)
    if head_path.exists() and head_path.read_text().strip() == snapshot_id:
        remaining = list_snapshots(root=root)
        if remaining:
            atomic_write_text(head_path, remaining[0]["id"] + "\n")
        else:
            head_path.unlink()


def rename_snapshot(old_id: str, new_id: str, root: Path) -> str:
    validate_snapshot_id(old_id)
    validate_snapshot_id(new_id)
    store_dir = _store_root(root)
    old_path = _validated_safe_path(store_dir.to_path() / "snapshots" / f"{old_id}.json", root)
    new_path = _validated_safe_path(store_dir.to_path() / "snapshots" / f"{new_id}.json", root)
    if not old_path.exists():
        raise ObjectNotFoundError(f"Snapshot not found: {old_id}")
    if new_path.exists():
        raise SnapshotExistsError(f"Snapshot '{new_id}' already exists.")
    data = old_path.read_text()
    manifest = json.loads(data)
    manifest["id"] = new_id
    manifest["name"] = new_id
    atomic_write_text(new_path, json.dumps(manifest, indent=2) + "\n")
    old_path.unlink()
    head_path = _validated_safe_path(store_dir.to_path() / "HEAD", root)
    if head_path.exists() and head_path.read_text().strip() == old_id:
        atomic_write_text(head_path, new_id + "\n")
    return new_id


def _count_objects(objects_dir: SafePath) -> tuple[int, int]:
    objects_count = 0
    total_bytes = 0
    if objects_dir.is_dir():
        for obj_file in objects_dir.rglob("*"):
            if obj_file.is_file():
                objects_count += 1
                with contextlib.suppress(OSError):
                    total_bytes += obj_file.stat().st_size
    return objects_count, total_bytes


def _count_unique_bytes(referenced_hashes, store_dir):
    unique_bytes = 0
    for obj_hash in referenced_hashes:
        obj_path = _hash_path(store_dir, obj_hash, mkdir=False)
        if obj_path.exists():
            with contextlib.suppress(OSError):
                unique_bytes += obj_path.stat().st_size
    return unique_bytes


def _remove_orphan_objects(objects_dir, referenced):
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
    return removed, freed_bytes


def _cleanup_empty_dirs(objects_dir):
    for subdir in sorted(objects_dir.glob("*"), reverse=True):
        if subdir.is_dir():
            with contextlib.suppress(OSError):
                subdir.to_path().rmdir()


def gc(root: Path) -> dict:
    store_dir = _store_root(root)
    objects_dir = store_dir / "objects"
    if not objects_dir.is_dir():
        return {"removed": 0, "freed_bytes": 0}
    manifests = _load_all_manifests(store_dir)
    referenced = _collect_referenced_hashes(manifests)
    removed, freed_bytes = _remove_orphan_objects(objects_dir, referenced)
    _cleanup_empty_dirs(objects_dir)
    return {"removed": removed, "freed_bytes": freed_bytes}


def stats(root: Path) -> dict:
    store_dir = _store_root(root)
    objects_dir = store_dir / "objects"
    manifests = _load_all_manifests(store_dir)
    snapshots_count = len(manifests)
    objects_count, total_bytes = _count_objects(objects_dir)
    referenced_hashes = _collect_referenced_hashes(manifests)
    unique_bytes = _count_unique_bytes(referenced_hashes, store_dir)
    dedup_pct = round((1 - unique_bytes / total_bytes) * 100, 1) if total_bytes > 0 else 0.0
    return {
        "snapshots": snapshots_count,
        "objects": objects_count,
        "total_bytes": total_bytes,
        "unique_bytes": unique_bytes,
        "dedup_pct": dedup_pct,
    }
