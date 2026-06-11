# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Public API data classes for arachna v2.0.0.

All return types for the public watch and collect APIs.
Use dataclasses for type safety and IDE autocompletion.
"""

from dataclasses import dataclass, field


@dataclass
class SnapshotInfo:
    """Information about a stored snapshot.

    Returned by list_snapshots() and snapshot_info().

    Attributes:
        id: Snapshot ID (same as name).
        name: Human-readable name, or None for legacy snapshots.
        created: ISO 8601 creation timestamp.
        profile: Full profile dict stored in the snapshot manifest.
        file_count: Number of files in the snapshot.
        pre_commands_count: Number of pre_commands outputs stored.
        command_count: Number of command outputs stored (0 or 1).
    """

    id: str
    name: str | None
    created: str
    profile: dict
    file_count: int
    pre_commands_count: int
    command_count: int


@dataclass
class DiffStats:
    """Aggregate statistics for a diff result.

    Attributes:
        modified: Count of modified files.
        added: Count of newly added files.
        deleted: Count of deleted files.
        renamed: Count of renamed files (detected by hash or similarity).
        moved: Count of moved files (same name, different directory).
        tokens: Total token count of all diff content.
    """

    modified: int = 0
    added: int = 0
    deleted: int = 0
    renamed: int = 0
    moved: int = 0
    tokens: int = 0


@dataclass
class DiffSection:
    """A single file change within a diff.

    Attributes:
        type: Change type — "modified", "added", "deleted",
              "renamed", "moved", or "header" (group heading).
        path: Current file path.
        old_path: Previous path (only for renames/moves).
        similarity: Similarity ratio 0.0-1.0 (only for renames/moves).
        content: Formatted diff content for this section.
    """

    type: str
    path: str
    old_path: str | None = None
    similarity: float | None = None
    content: str = ""


@dataclass
class DiffResult:
    """Complete result of a diff operation.

    Returned by compute_diff().

    Attributes:
        snapshot_id: ID of the source snapshot (--from).
        to_snapshot_id: ID of the target snapshot (--to), or None.
        stats: Aggregate statistics for the diff.
        sections: List of DiffSection objects with diff content.
    """

    snapshot_id: str
    to_snapshot_id: str | None
    stats: DiffStats
    sections: list[DiffSection] = field(default_factory=list)


@dataclass
class CollectResult:
    """Result of a collection operation.

    Returned by collect().

    Attributes:
        parts: List of output file contents as strings.
        files: List of created file paths.
        tokens: Total token count across all output files.
    """

    parts: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    tokens: int = 0


@dataclass
class StoreStats:
    """Statistics about the content-addressable store.

    Returned by store_stats().

    Attributes:
        snapshots: Number of snapshots in the store.
        objects: Number of object files on disk.
        total_bytes: Total disk usage in bytes.
        unique_bytes: Size of unique content (deduplicated).
        dedup_pct: Deduplication percentage (0.0-100.0).
                   Higher is better — more sharing between snapshots.
    """

    snapshots: int = 0
    objects: int = 0
    total_bytes: int = 0
    unique_bytes: int = 0
    dedup_pct: float = 0.0


@dataclass
class GCResult:
    """Result of a garbage collection operation.

    Returned by store_gc().

    Attributes:
        removed_objects: Number of unreferenced objects deleted.
        freed_bytes: Total bytes freed.
    """

    removed_objects: int = 0
    freed_bytes: int = 0
