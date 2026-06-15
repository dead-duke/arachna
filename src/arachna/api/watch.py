# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Public Watch API for arachna v4.0.0."""

import logging
from pathlib import Path

from ..config.config import get_profile
from ..domain.api_types import (
    DiffResult,
    DiffSection,
    DiffStats,
    GCResult,
    SnapshotInfo,
    StoreStats,
)
from ..watch.differ import compute_diff_stats
from ..watch.differ_structural import structural_diff_sections
from ..watch.store import (
    create_snapshot as _store_create,
)
from ..watch.store import (
    delete_snapshot as _store_delete,
)
from ..watch.store import (
    gc as _store_gc,
)
from ..watch.store import (
    list_snapshots as _store_list,
)
from ..watch.store import (
    load_snapshot as _store_load,
)
from ..watch.store import (
    stats as _store_stats,
)
from ..watch.store import (
    update_snapshot as _store_update,
)
from ..watch.store_errors import ObjectNotFoundError as _ObjectNotFoundError
from ..watch.store_errors import SnapshotExistsError as _StoreSnapshotExistsError
from ..watch.watcher import _apply_repo_map_to_sections, _collect_snapshot_content
from ..watch.watcher import compute_diff as _watcher_compute_diff
from .api_errors import (
    ProfileNotFoundError,
    SnapshotExistsError,
    SnapshotNotFoundError,
)

logger = logging.getLogger("arachna.watch")


def create_snapshot(root: Path, profile: str | dict = "full", name: str | None = None) -> str:
    if name is None:
        raise ValueError("name is required for create_snapshot()")
    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile, root=root)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    else:
        profile_dict = profile
    files, pre_commands_data, command_data = _collect_snapshot_content(profile_dict, root)
    try:
        return _store_create(
            files,
            root=root,
            profile_dict=profile_dict,
            name=name,
            pre_commands=pre_commands_data if pre_commands_data else None,
            command=command_data if command_data else None,
        )
    except _StoreSnapshotExistsError as e:
        raise SnapshotExistsError(str(e)) from e


def list_snapshots(root: Path) -> list[SnapshotInfo]:
    manifests = _store_list(root=root)
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


def update_snapshot(snapshot_id: str, root: Path, profile: str | dict | None = None) -> str:
    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile, root=root)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    elif isinstance(profile, dict):
        profile_dict = profile
    else:
        profile_dict = None
    try:
        manifest = _store_load(snapshot_id, root=root)
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
    files, pre_commands_data, command_data = _collect_snapshot_content(profile_dict, root)
    try:
        return _store_update(
            snapshot_id,
            files,
            root=root,
            profile_dict=profile_dict,
            pre_commands=pre_commands_data if pre_commands_data else None,
            command=command_data if command_data else None,
        )
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e


def delete_snapshot(snapshot_id: str, root: Path) -> None:
    try:
        _store_delete(snapshot_id, root=root)
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e


def snapshot_info(snapshot_id: str, root: Path) -> SnapshotInfo:
    try:
        manifest = _store_load(snapshot_id, root=root)
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
    root: Path,
    snapshot_id: str | None = None,
    profile: str | dict = "full",
    fmt: str = "markdown",
    to_snapshot_id: str | None = None,
    mode: str = "full",
    flat: bool = False,
    streaming: bool = False,
) -> DiffResult:
    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile, root=root)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    else:
        profile_dict = profile
    if snapshot_id is None:
        snaps = _store_list(root=root)
        if len(snaps) == 0:
            raise SnapshotNotFoundError("No snapshots found.")
        elif len(snaps) == 1:
            snapshot_id = snaps[0]["id"]
        else:
            raise ValueError(
                f"Multiple snapshots found. Specify snapshot_id from: {', '.join(s['id'] for s in snaps)}"
            )
    sections = _watcher_compute_diff(
        snapshot_id,
        profile_dict,
        root,
        fmt=fmt,
        to_snapshot_id=to_snapshot_id,
        flat=flat,
        streaming=streaming,
    )
    if mode == "structural" and sections:
        sections = structural_diff_sections(sections, fmt)
    elif mode == "repo-map" and sections:
        sections = _apply_repo_map_to_sections(
            sections, snapshot_id, to_snapshot_id, profile_dict, root
        )
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


def store_stats(root: Path) -> StoreStats:
    raw = _store_stats(root=root)
    return StoreStats(
        snapshots=raw["snapshots"],
        objects=raw["objects"],
        total_bytes=raw["total_bytes"],
        unique_bytes=raw["unique_bytes"],
        dedup_pct=raw["dedup_pct"],
    )


def store_gc(root: Path) -> GCResult:
    raw = _store_gc(root=root)
    return GCResult(removed_objects=raw["removed"], freed_bytes=raw["freed_bytes"])
