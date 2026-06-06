"""Public Watch API for arachna v2.0.0.

Provides programmatic access to snapshots, diffs, and store operations.
All functions return structured data, raise specific exceptions,
and never call sys.exit().

Usage:
    from arachna import watch

    # Create a snapshot
    sid = watch.create_snapshot(profile="full", name="baseline")

    # List all snapshots
    for snap in watch.list_snapshots():
        print(f"{snap.id}: {snap.file_count} files")

    # Compute diff
    result = watch.compute_diff(snapshot_id="baseline", profile="full")
    print(f"Modified: {result.stats.modified}, Added: {result.stats.added}")

    # Store statistics
    stats = watch.store_stats()
    print(f"Dedup: {stats.dedup_pct}%")
"""

from pathlib import Path

from .api_errors import (
    ProfileNotFoundError,
    SnapshotExistsError,
    SnapshotNotFoundError,
)
from .api_types import (
    DiffResult,
    DiffSection,
    DiffStats,
    GCResult,
    SnapshotInfo,
    StoreStats,
)
from .config import get_profile
from .differ import compute_diff_stats
from .store import (
    create_snapshot as _store_create,
)
from .store import (
    delete_snapshot as _store_delete,
)
from .store import (
    gc as _store_gc,
)
from .store import (
    list_snapshots as _store_list,
)
from .store import (
    load_snapshot as _store_load,
)
from .store import (
    stats as _store_stats,
)
from .store import (
    update_snapshot as _store_update,
)
from .store_errors import ObjectNotFoundError as _ObjectNotFoundError
from .store_errors import SnapshotExistsError as _StoreSnapshotExistsError
from .watcher import (
    _collect_snapshot_content,
)
from .watcher import (
    compute_diff as _watcher_compute_diff,
)

# ── Snapshot API ───────────────────────────────────────────────────


def create_snapshot(profile: str | dict = "full", name: str | None = None) -> str:
    """Create a named snapshot of the current project state.

    Walks all files matching the profile and stores them in the
    content-addressable store under .arachna/store/. Files are
    deduplicated by SHA256 hash — identical content across snapshots
    is stored only once.

    The full profile dict (directories, patterns, files, etc.) is
    stored in the manifest for later use by compute_diff() without
    needing to specify --profile again.

    Args:
        profile: Profile name from .arachna.json (e.g. "full", "code")
                 or a profile dict with directories/patterns/files.
                 Default: "full".
        name: Snapshot name. Required — used as the snapshot ID.
              Must be unique. Use update_snapshot() to refresh an
              existing snapshot.

    Returns:
        Snapshot ID (same as name).

    Raises:
        ProfileNotFoundError: Profile name not found in .arachna.json.
        SnapshotExistsError: A snapshot with this name already exists.
        ValueError: name is None.

    Example:
        >>> sid = watch.create_snapshot(profile="full", name="before-refactor")
        >>> print(sid)
        'before-refactor'
    """
    if name is None:
        raise ValueError("name is required for create_snapshot()")

    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    else:
        profile_dict = profile

    files, pre_commands_data, command_data = _collect_snapshot_content(profile_dict)

    try:
        return _store_create(
            files,
            profile_dict=profile_dict,
            name=name,
            pre_commands=pre_commands_data if pre_commands_data else None,
            command=command_data if command_data else None,
        )
    except _StoreSnapshotExistsError as e:
        raise SnapshotExistsError(str(e)) from e


def list_snapshots() -> list[SnapshotInfo]:
    """List all snapshots in the store.

    Returns snapshots sorted by creation time, newest first.
    Each SnapshotInfo contains the snapshot id, optional name,
    creation timestamp, full profile dict, and counts of
    files, pre_commands outputs, and command outputs.

    Returns:
        List of SnapshotInfo objects, newest first.
        Empty list if no snapshots exist.

    Example:
        >>> snaps = watch.list_snapshots()
        >>> for s in snaps:
        ...     print(f"{s.id}: {s.file_count} files, created {s.created}")
    """
    manifests = _store_list()
    result = []
    for m in manifests:
        result.append(
            SnapshotInfo(
                id=m["id"],
                name=m.get("name"),
                created=m.get("created", ""),
                profile=m.get("profile", {}),
                file_count=len(m.get("files", {})),
                pre_commands_count=len(m.get("pre_commands", {})),
                command_count=len(m.get("command", {})),
            )
        )
    return result


def update_snapshot(snapshot_id: str, profile: str | dict | None = None) -> str:
    """Update an existing snapshot with the current project state.

    Re-scans all files matching the profile and replaces the snapshot
    content. Preserves the snapshot name and ID. Updates the creation
    timestamp to the current time.

    Args:
        snapshot_id: ID of the snapshot to update.
        profile: Optional new profile name or dict. If None, reuses
                 the profile stored in the snapshot manifest.

    Returns:
        Snapshot ID (same as input).

    Raises:
        SnapshotNotFoundError: Snapshot does not exist.
        ProfileNotFoundError: Profile name not found in .arachna.json.
        ValueError: Snapshot has legacy format (string profile) and
                    no profile argument was provided.

    Example:
        >>> watch.update_snapshot("baseline", profile="full")
        'baseline'
    """
    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    elif isinstance(profile, dict):
        profile_dict = profile
    else:
        profile_dict = None

    try:
        manifest = _store_load(snapshot_id)
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e

    if profile_dict is None:
        stored = manifest.get("profile", {})
        if isinstance(stored, dict):
            profile_dict = stored
        else:
            raise ValueError(
                f"Snapshot '{snapshot_id}' has legacy format (profile is a string). "
                f"Provide profile explicitly."
            )

    files, pre_commands_data, command_data = _collect_snapshot_content(profile_dict)

    try:
        return _store_update(
            snapshot_id,
            files,
            profile_dict=profile_dict,
            pre_commands=pre_commands_data if pre_commands_data else None,
            command=command_data if command_data else None,
        )
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e


def delete_snapshot(snapshot_id: str) -> None:
    """Delete a snapshot from the store.

    Removes only the snapshot manifest. The actual file contents
    (objects) remain in the store if referenced by other snapshots.
    Use store_gc() to remove unreferenced objects and free disk space.

    Args:
        snapshot_id: ID of the snapshot to delete.

    Raises:
        SnapshotNotFoundError: Snapshot does not exist.

    Example:
        >>> watch.delete_snapshot("old-baseline")
    """
    try:
        _store_delete(snapshot_id)
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e


def snapshot_info(snapshot_id: str) -> SnapshotInfo:
    """Get detailed information about a snapshot.

    Reads the snapshot manifest from the store and returns structured
    data including the full profile dict, file count, and counts of
    pre_commands and command outputs.

    Args:
        snapshot_id: ID of the snapshot to inspect.

    Returns:
        SnapshotInfo with id, name, created timestamp, profile dict,
        file_count, pre_commands_count, and command_count.

    Raises:
        SnapshotNotFoundError: Snapshot does not exist.

    Example:
        >>> info = watch.snapshot_info("baseline")
        >>> print(f"Profile dirs: {info.profile.get('directories', [])}")
        >>> print(f"Files: {info.file_count}")
    """
    try:
        manifest = _store_load(snapshot_id)
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e

    return SnapshotInfo(
        id=manifest["id"],
        name=manifest.get("name"),
        created=manifest.get("created", ""),
        profile=manifest.get("profile", {}),
        file_count=len(manifest.get("files", {})),
        pre_commands_count=len(manifest.get("pre_commands", {})),
        command_count=len(manifest.get("command", {})),
    )


# ── Diff API ───────────────────────────────────────────────────────


def compute_diff(
    snapshot_id: str | None = None,
    profile: str | dict = "full",
    fmt: str = "markdown",
    to_snapshot_id: str | None = None,
    mode: str = "full",
    flat: bool = False,
) -> DiffResult:
    """Compute diff between a snapshot and current files or another snapshot.

    Compares the project state stored in a snapshot against either
    the current files on disk (default) or another snapshot
    (cross-snapshot diff via to_snapshot_id).

    Supports three diff modes:
    - "full": Line-based difflib diff. Shows REMOVED and ADDED line
      ranges. Default, backward compatible.
    - "structural": Block-level diff that understands code structure.
      Shows MODIFIED/DELETED/ADDED functions and classes with
      signature and body changes.
    - "repo-map": Signatures only, no diff content. Lightweight
      overview of what changed at the function/class level.

    Output is grouped by change type by default (renamed, moved,
    modified, added, deleted) with a summary header. Use flat=True
    for a flat list of sections.

    Args:
        snapshot_id: ID of the snapshot to diff from. If None,
            auto-selects the single snapshot or raises if multiple
            snapshots exist.
        profile: Profile name or dict for the current file state.
            Ignored for cross-snapshot diffs (to_snapshot_id is set).
        fmt: Output format — "markdown" (default) or "xml".
        to_snapshot_id: Optional second snapshot ID. When set, diffs
            between two snapshots instead of snapshot vs current files.
        mode: Diff mode — "full", "structural", or "repo-map".
        flat: If True, flat list of DiffSections. If False (default),
            sections grouped by type with a summary header.

    Returns:
        DiffResult with snapshot_id, to_snapshot_id, stats (DiffStats),
        and sections (list of DiffSection).

    Raises:
        SnapshotNotFoundError: Snapshot not found or no snapshots exist.
        ProfileNotFoundError: Profile name not found in .arachna.json.
        ValueError: Multiple snapshots exist and snapshot_id is None.

    Example:
        >>> # Diff from snapshot to current files
        >>> result = watch.compute_diff(snapshot_id="baseline", profile="full")
        >>> print(f"Modified: {result.stats.modified} files")
        >>>
        >>> # Cross-snapshot diff
        >>> result = watch.compute_diff(
        ...     snapshot_id="v1", to_snapshot_id="v2", profile="full"
        ... )
        >>>
        >>> # Structural mode
        >>> result = watch.compute_diff(
        ...     snapshot_id="baseline", profile="full", mode="structural"
        ... )
    """
    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    else:
        profile_dict = profile

    # Auto-select snapshot if not specified
    if snapshot_id is None:
        snaps = _store_list()
        if len(snaps) == 0:
            raise SnapshotNotFoundError(
                "No snapshots found. Create one with create_snapshot() first."
            )
        elif len(snaps) == 1:
            snapshot_id = snaps[0]["id"]
        else:
            ids = [s["id"] for s in snaps]
            raise ValueError(
                f"Multiple snapshots found. Specify snapshot_id from: {', '.join(ids)}"
            )

    sections = _watcher_compute_diff(
        snapshot_id,
        profile_dict,
        fmt=fmt,
        to_snapshot_id=to_snapshot_id,
        flat=flat,
    )

    # Apply structural diff if requested
    if mode == "structural" and sections:
        sections = _apply_structural_diff(sections, fmt)
    elif mode == "repo-map" and sections:
        sections = _apply_repo_map_diff(sections)

    # Convert to API types
    api_sections = [
        DiffSection(
            type=s.type,
            path=s.path,
            old_path=s.old_path,
            similarity=s.similarity,
            content=s.content,
        )
        for s in sections
    ]

    raw_stats = compute_diff_stats(sections)
    stats = DiffStats(
        modified=raw_stats["modified"],
        added=raw_stats["added"],
        deleted=raw_stats["deleted"],
        renamed=raw_stats.get("renamed", 0),
        moved=raw_stats.get("moved", 0),
        tokens=raw_stats["tokens"],
    )

    return DiffResult(
        snapshot_id=snapshot_id,
        to_snapshot_id=to_snapshot_id,
        stats=stats,
        sections=api_sections,
    )


def _apply_structural_diff(sections: list, fmt: str) -> list:
    """Apply structural diff to sections."""
    from .differ_structural import structural_diff_sections

    return structural_diff_sections(sections, fmt)


def _apply_repo_map_diff(sections: list) -> list:
    """Apply repo-map mode to diff sections (signatures only)."""

    from .formatter import lang_for_path
    from .splitter import extract_signatures

    result = []
    for s in sections:
        if s.type in ("header",) or not s.path:
            result.append(s)
            continue
        lang = lang_for_path(Path(s.path))
        sigs = extract_signatures(s.content, lang)
        s.content = sigs
        result.append(s)
    return result


# ── Store API ──────────────────────────────────────────────────────


def store_stats() -> StoreStats:
    """Get statistics about the content-addressable store.

    Returns counts of snapshots, objects, total disk usage,
    unique content size, and deduplication percentage.
    High dedup_pct means many snapshots share identical files —
    the store is working efficiently.

    Returns:
        StoreStats with snapshots, objects, total_bytes,
        unique_bytes, and dedup_pct (0.0 to 100.0).

    Example:
        >>> stats = watch.store_stats()
        >>> print(f"{stats.snapshots} snapshots")
        >>> print(f"{stats.dedup_pct}% deduplication")
        >>> print(f"{stats.total_bytes} bytes on disk")
    """
    raw = _store_stats()
    return StoreStats(
        snapshots=raw["snapshots"],
        objects=raw["objects"],
        total_bytes=raw["total_bytes"],
        unique_bytes=raw["unique_bytes"],
        dedup_pct=raw["dedup_pct"],
    )


def store_gc() -> GCResult:
    """Garbage collect unreferenced objects from the store.

    Removes object files that are not referenced by any snapshot.
    Safe to call at any time — only data with no remaining references
    is deleted. Run periodically to free disk space after deleting
    old snapshots.

    Returns:
        GCResult with removed_objects count and freed_bytes.

    Example:
        >>> result = watch.store_gc()
        >>> if result.removed_objects > 0:
        ...     print(f"Freed {result.freed_bytes} bytes")
        ... else:
        ...     print("Nothing to collect")
    """
    raw = _store_gc()
    return GCResult(
        removed_objects=raw["removed"],
        freed_bytes=raw["freed_bytes"],
    )
