"""Content-addressable store for Watch snapshots.

Storage layout under .arachna/ (created lazily on first write):

    .arachna/
      .gitignore          # "*" — never commit this directory
      store/
        objects/
          ab/cd1234...    # zlib-compressed file content (if compression saves space)
        snapshots/
          20260603T103000.json   # manifest: {path: hash, ...}
        HEAD                     # text file with latest snapshot ID

Objects are stored by SHA256 hash. The hash is computed BEFORE optional
zlib compression — so the hash identifies the content, not the encoding.
"""

import contextlib
import hashlib
import json
import logging
import os
import zlib
from datetime import datetime
from pathlib import Path

from .store_errors import CorruptedStoreError, ObjectNotFoundError, SnapshotExistsError

logger = logging.getLogger("arachna.store")


def _store_root() -> Path:
    """Return .arachna/store/ directory, creating it lazily.

    On first creation, writes .arachna/.gitignore with "*" to prevent
    accidental commits of the store directory.
    """
    cwd = Path.cwd()
    arachna_dir = cwd / ".arachna"
    gitignore = arachna_dir / ".gitignore"

    if not arachna_dir.is_dir():
        arachna_dir.mkdir(parents=True, exist_ok=True)
        gitignore.write_text("*\n")

    store_dir = arachna_dir / "store"
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir


def _hash_path(store_dir: Path, object_hash: str, mkdir: bool = False) -> Path:
    """Return path to object file: objects/ab/cd1234...

    Args:
        store_dir: Store root directory.
        object_hash: SHA256 hex digest.
        mkdir: If True, create the prefix directory. Use False for reads.
    """
    objects_dir = store_dir / "objects"
    prefix = object_hash[:2]
    rest = object_hash[2:]
    obj_dir = objects_dir / prefix
    if mkdir:
        obj_dir.mkdir(parents=True, exist_ok=True)
    return obj_dir / rest


def write_object(data: bytes) -> str:
    """Store content in objects/, return SHA256 hash.

    Hash is computed on original data BEFORE compression.
    If zlib compression reduces size, store compressed.
    Otherwise store raw.
    """
    object_hash = hashlib.sha256(data).hexdigest()
    store_dir = _store_root()
    path = _hash_path(store_dir, object_hash, mkdir=True)

    if path.exists():
        return object_hash

    compressed = zlib.compress(data)
    if len(compressed) < len(data):
        path.write_bytes(compressed)
    else:
        path.write_bytes(data)

    return object_hash


def read_object(object_hash: str) -> bytes:
    """Read from objects/, decompress if needed.

    Auto-detects compression: tries zlib.decompress first,
    falls back to raw bytes if decompression fails (data stored uncompressed).

    Raises:
        ObjectNotFoundError: object doesn't exist.
        CorruptedStoreError: content doesn't match hash.
    """
    store_dir = _store_root()
    path = _hash_path(store_dir, object_hash, mkdir=False)

    if not path.exists():
        raise ObjectNotFoundError(f"Object not found: {object_hash}")

    raw = path.read_bytes()

    # Auto-detect compression: try zlib, fallback to raw
    try:
        data = zlib.decompress(raw)
    except zlib.error:
        data = raw

    # Verify integrity
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != object_hash:
        raise CorruptedStoreError(
            f"Object {object_hash} is corrupted: expected hash {object_hash}, "
            f"got {actual_hash}. The file may have been modified or is not "
            f"a valid arachna object."
        )

    return data


def create_snapshot(
    files: dict[str, str],
    profile_dict: dict | None = None,
    profile: str = "full",
    name: str | None = None,
    pre_commands: dict[str, str] | None = None,
    command: dict[str, str] | None = None,
) -> str:
    """Create a snapshot manifest and return its ID.

    Args:
        files: {path: content} dict of all files to snapshot.
        profile_dict: full profile dict (directories, patterns, etc.).
            Stored in manifest for later use by --diff without --profile.
        profile: profile name string (legacy, used if profile_dict not given).
        name: human-readable name. Required for named snapshots.
            If None, timestamp YYYYMMDDTHHMMSS is used as ID.
        pre_commands: optional {label: "sha256:hash"} for pre_commands output.
        command: optional {label: "sha256:hash"} for command output.

    Returns:
        Snapshot ID (name if given, else timestamp YYYYMMDDTHHMMSS).

    Raises:
        SnapshotExistsError: if a snapshot with the given name already exists.
    """
    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    snapshot_id = name if name else datetime.now().strftime("%Y%m%dT%H%M%S")

    # Check for duplicate name
    manifest_path = snapshots_dir / f"{snapshot_id}.json"
    if name and manifest_path.exists():
        raise SnapshotExistsError(
            f"Snapshot '{name}' already exists. Use 'arachna --snapshot update {name}' "
            f"to update it, or delete it first."
        )

    # Store all file contents, collect hashes
    file_hashes = {}
    for path, content in files.items():
        obj_hash = write_object(content.encode("utf-8"))
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

    manifest_path.write_text(json.dumps(manifest, indent=2))

    # Update HEAD
    head_path = store_dir / "HEAD"
    head_path.write_text(snapshot_id)

    return snapshot_id


def update_snapshot(
    snapshot_id: str,
    files: dict[str, str],
    profile_dict: dict | None = None,
    pre_commands: dict[str, str] | None = None,
    command: dict[str, str] | None = None,
) -> str:
    """Update an existing snapshot with new content.

    Preserves snapshot ID and name. Updates created timestamp.
    If profile_dict is given, updates stored profile.
    Otherwise keeps existing profile from manifest.

    Args:
        snapshot_id: ID of the snapshot to update.
        files: new {path: content} dict.
        profile_dict: optional new profile dict.
        pre_commands: optional new pre_commands data.
        command: optional new command data.

    Returns:
        Snapshot ID (same as input).

    Raises:
        ObjectNotFoundError: if snapshot doesn't exist.
    """
    manifest = load_snapshot(snapshot_id)

    # Store new file contents
    file_hashes = {}
    for path, content in files.items():
        obj_hash = write_object(content.encode("utf-8"))
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

    store_dir = _store_root()
    manifest_path = store_dir / "snapshots" / f"{snapshot_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    # Update HEAD if this was HEAD
    head_path = store_dir / "HEAD"
    if head_path.exists() and head_path.read_text().strip() == snapshot_id:
        head_path.write_text(snapshot_id)

    return snapshot_id


def load_snapshot(snapshot_id: str) -> dict:
    """Load manifest from snapshots/<id>.json.

    Returns full manifest dict.

    Raises:
        ObjectNotFoundError: snapshot doesn't exist.
    """
    store_dir = _store_root()
    manifest_path = store_dir / "snapshots" / f"{snapshot_id}.json"

    if not manifest_path.exists():
        raise ObjectNotFoundError(f"Snapshot not found: {snapshot_id}")

    return json.loads(manifest_path.read_text())


def list_snapshots() -> list[dict]:
    """Return list of all manifest dicts, sorted by creation time descending."""
    store_dir = _store_root()
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
    """Load all manifest dicts from snapshots/. Shared by stats() and gc()."""
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
    """Collect all referenced SHA256 hashes from manifests.

    Extracts hashes from files, pre_commands, and command fields.
    Shared by stats() and gc() to deduplicate hash collection logic.

    Args:
        manifests: List of manifest dicts from _load_all_manifests().

    Returns:
        Set of SHA256 hex digest strings (without "sha256:" prefix).
    """
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


def delete_snapshot(snapshot_id: str) -> None:
    """Delete manifest file. Objects remain (cleaned by GC).

    Raises:
        ObjectNotFoundError: snapshot doesn't exist.
    """
    store_dir = _store_root()
    manifest_path = store_dir / "snapshots" / f"{snapshot_id}.json"

    if not manifest_path.exists():
        raise ObjectNotFoundError(f"Snapshot not found: {snapshot_id}")

    manifest_path.unlink()

    # Clear HEAD if it pointed to this snapshot
    head_path = store_dir / "HEAD"
    if head_path.exists() and head_path.read_text().strip() == snapshot_id:
        # Point HEAD to the latest remaining snapshot, or remove
        remaining = list_snapshots()
        if remaining:
            head_path.write_text(remaining[0]["id"])
        else:
            head_path.unlink()


def rename_snapshot(old_id: str, new_id: str) -> str:
    """Rename a snapshot — updates manifest id/name and file name.

    Updates HEAD if it pointed to the old snapshot ID.

    Args:
        old_id: current snapshot ID.
        new_id: new snapshot ID.

    Returns:
        New snapshot ID.

    Raises:
        ObjectNotFoundError: if old_id doesn't exist.
        SnapshotExistsError: if new_id already exists.
    """
    store_dir = _store_root()
    snapshots_dir = store_dir / "snapshots"
    old_path = snapshots_dir / f"{old_id}.json"
    new_path = snapshots_dir / f"{new_id}.json"

    if not old_path.exists():
        raise ObjectNotFoundError(f"Snapshot not found: {old_id}")

    if new_path.exists():
        raise SnapshotExistsError(
            f"Snapshot '{new_id}' already exists. "
            f"Use a different name or delete the existing snapshot first."
        )

    # Load manifest, update id and name
    manifest = json.loads(old_path.read_text())
    manifest["id"] = new_id
    manifest["name"] = new_id

    # Write to new path
    new_path.write_text(json.dumps(manifest, indent=2))

    # Remove old file
    old_path.unlink()

    # Update HEAD if it pointed to old_id
    head_path = store_dir / "HEAD"
    if head_path.exists() and head_path.read_text().strip() == old_id:
        head_path.write_text(new_id)

    return new_id


def gc() -> dict:
    """Garbage collection: delete unreferenced objects and empty dirs.

    Finds all hashes referenced across all manifests,
    deletes object files not in the referenced set.
    Removes empty subdirectories in objects/ after cleanup.

    Returns:
        {removed: N, freed_bytes: M}
    """
    store_dir = _store_root()
    objects_dir = store_dir / "objects"

    if not objects_dir.is_dir():
        return {"removed": 0, "freed_bytes": 0}

    # Collect all referenced hashes from all manifests
    manifests = _load_all_manifests(store_dir)
    referenced = _collect_referenced_hashes(manifests)

    # Delete unreferenced objects
    removed = 0
    freed_bytes = 0
    for obj_file in objects_dir.rglob("*"):
        if not obj_file.is_file():
            continue
        # Object path: objects/ab/cd1234... → hash = ab + cd1234...
        rel = obj_file.relative_to(objects_dir)
        obj_hash = str(rel).replace(os.sep, "")
        if obj_hash not in referenced:
            with contextlib.suppress(OSError):
                freed_bytes += obj_file.stat().st_size
            obj_file.unlink()
            removed += 1

    # Clean up empty subdirectories
    for subdir in sorted(objects_dir.glob("*"), reverse=True):
        if subdir.is_dir():
            with contextlib.suppress(OSError):
                subdir.rmdir()

    return {"removed": removed, "freed_bytes": freed_bytes}


def stats() -> dict:
    """Return store statistics.

    Returns:
        {snapshots: N, objects: M, total_bytes: X, unique_bytes: Y, dedup_pct: Z}
    """
    store_dir = _store_root()
    objects_dir = store_dir / "objects"

    # Load manifests once
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

    # Collect referenced hashes from manifests
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
