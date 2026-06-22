"""Public Snapshot API."""

import logging
from pathlib import Path

from ..config import CollectionMode, OutputFormat
from ..config.profile_config import ProfileConfig
from ..domain.api_types import (
    DiffResult,
    DiffSection,
    DiffStats,
    GCResult,
    SnapshotInfo,
    StoreStats,
)
from ..domain.differ_stats import compute_diff_stats
from ..snapshot.diff.differ_structural import structural_diff_sections
from ..snapshot.diff.snapshot_diff import collect_snapshot_content
from ..snapshot.diff.snapshot_diff import compute_diff as _snapshot_compute_diff
from ..snapshot.diff.snapshot_diff_repo_map import apply_repo_map_to_sections
from ..snapshot.store.store import create_snapshot as _store_create
from ..snapshot.store.store import delete_snapshot as _store_delete
from ..snapshot.store.store import gc as _store_gc
from ..snapshot.store.store import list_snapshots as _store_list
from ..snapshot.store.store import load_snapshot as _store_load
from ..snapshot.store.store import stats as _store_stats
from ..snapshot.store.store import update_snapshot as _store_update
from ..snapshot.store.store_errors import ObjectNotFoundError as _ObjectNotFoundError
from ..snapshot.store.store_errors import SnapshotExistsError as _StoreSnapshotExistsError
from .api_errors import SnapshotExistsError, SnapshotNotFoundError

logger = logging.getLogger("arachna.snapshot")


def create_snapshot(root: Path, profile: ProfileConfig, name: str | None = None) -> str:
    if name is None:
        raise ValueError("name is required for create_snapshot()")
    files, pre_commands_data, command_data = collect_snapshot_content(profile, root)
    try:
        return _store_create(
            files,
            root=root,
            profile_dict=profile.to_dict(),
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


def update_snapshot(
    snapshot_id: str,
    root: Path,
    profile: ProfileConfig | None = None,
) -> str:
    profile_dict = profile
    try:
        manifest = _store_load(snapshot_id, root=root)
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e
    if profile_dict is None:
        stored = manifest.get("profile", {})
        if isinstance(stored, dict):
            profile_dict = ProfileConfig.from_dict(stored)
        else:
            raise ValueError(
                f"Snapshot '{snapshot_id}' has legacy format. Provide profile explicitly."
            )
    files, pre_commands_data, command_data = collect_snapshot_content(profile_dict, root)
    try:
        return _store_update(
            snapshot_id,
            files,
            root=root,
            profile_dict=profile_dict.to_dict(),
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


def _resolve_snapshot_id(snapshot_id, root):
    if snapshot_id is not None:
        return snapshot_id
    snaps = _store_list(root=root)
    if len(snaps) == 0:
        raise SnapshotNotFoundError("No snapshots found.")
    elif len(snaps) == 1:
        return snaps[0]["id"]
    else:
        raise ValueError(
            f"Multiple snapshots found. Specify snapshot_id from: {', '.join(s['id'] for s in snaps)}"
        )


def _build_diff_sections(sections, mode: CollectionMode, snapshot_id, to_snapshot_id, root):
    if mode == "structural" and sections:
        sections = structural_diff_sections(sections, "markdown")
    elif mode == "repo-map" and sections:
        sections = apply_repo_map_to_sections(sections, snapshot_id, to_snapshot_id, root=root)
    return [
        DiffSection(
            type=s.type,
            path=s.path,
            old_path=s.old_path,
            similarity=s.similarity,
            content=s.content,
        )
        for s in sections
    ]


def compute_diff(
    root: Path,
    profile: ProfileConfig,
    snapshot_id: str | None = None,
    fmt: OutputFormat = "markdown",
    to_snapshot_id: str | None = None,
    mode: CollectionMode = "full",
    flat: bool = False,
    line_numbers: bool = False,
) -> DiffResult:
    snapshot_id = _resolve_snapshot_id(snapshot_id, root)
    sections = _snapshot_compute_diff(
        snapshot_id,
        profile,
        root,
        fmt=fmt,
        to_snapshot_id=to_snapshot_id,
        flat=flat,
        line_numbers=line_numbers,
    )
    api_sections = _build_diff_sections(sections, mode, snapshot_id, to_snapshot_id, root)
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
