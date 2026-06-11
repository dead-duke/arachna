# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Public Watch API for arachna v2.0.0."""

import logging

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
from .gatherer import _apply_repo_map_to_sections
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
from .watcher import _collect_snapshot_content
from .watcher import compute_diff as _watcher_compute_diff

logger = logging.getLogger("arachna.watch")


def create_snapshot(profile: str | dict = "full", name: str | None = None) -> str:
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
                f"Snapshot '{snapshot_id}' has legacy format. Provide profile explicitly."
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
    try:
        _store_delete(snapshot_id)
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e


def snapshot_info(snapshot_id: str) -> SnapshotInfo:
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


def compute_diff(
    snapshot_id: str | None = None,
    profile: str | dict = "full",
    fmt: str = "markdown",
    to_snapshot_id: str | None = None,
    mode: str = "full",
    flat: bool = False,
) -> DiffResult:
    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    else:
        profile_dict = profile
    if snapshot_id is None:
        snaps = _store_list()
        if len(snaps) == 0:
            raise SnapshotNotFoundError("No snapshots found.")
        elif len(snaps) == 1:
            snapshot_id = snaps[0]["id"]
        else:
            raise ValueError(
                f"Multiple snapshots found. Specify snapshot_id from: {', '.join(s['id'] for s in snaps)}"
            )
    sections = _watcher_compute_diff(
        snapshot_id, profile_dict, fmt=fmt, to_snapshot_id=to_snapshot_id, flat=flat
    )
    if mode == "structural" and sections:
        from .differ_structural import structural_diff_sections

        sections = structural_diff_sections(sections, fmt)
    elif mode == "repo-map" and sections:
        sections = _apply_repo_map_to_sections(sections, snapshot_id, to_snapshot_id, profile_dict)
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
        snapshot_id=snapshot_id, to_snapshot_id=to_snapshot_id, stats=stats, sections=api_sections
    )


def store_stats() -> StoreStats:
    raw = _store_stats()
    return StoreStats(
        snapshots=raw["snapshots"],
        objects=raw["objects"],
        total_bytes=raw["total_bytes"],
        unique_bytes=raw["unique_bytes"],
        dedup_pct=raw["dedup_pct"],
    )


def store_gc() -> GCResult:
    raw = _store_gc()
    return GCResult(removed_objects=raw["removed"], freed_bytes=raw["freed_bytes"])
