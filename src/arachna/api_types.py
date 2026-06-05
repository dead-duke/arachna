"""Public API data classes for arachna v2.0.0."""

from dataclasses import dataclass, field


@dataclass
class SnapshotInfo:
    """Information about a stored snapshot."""

    id: str
    name: str | None
    created: str
    profile: dict
    file_count: int
    pre_commands_count: int
    command_count: int


@dataclass
class DiffStats:
    """Aggregate statistics for a diff."""

    modified: int = 0
    added: int = 0
    deleted: int = 0
    renamed: int = 0
    moved: int = 0
    tokens: int = 0


@dataclass
class DiffSection:
    """A single file change in a diff."""

    type: str  # "modified" | "added" | "deleted" | "renamed" | "moved" | "header"
    path: str
    old_path: str | None = None
    similarity: float | None = None
    content: str = ""


@dataclass
class DiffResult:
    """Complete diff result."""

    snapshot_id: str
    to_snapshot_id: str | None
    stats: DiffStats
    sections: list[DiffSection] = field(default_factory=list)


@dataclass
class CollectResult:
    """Result of a collection operation."""

    parts: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    tokens: int = 0


@dataclass
class StoreStats:
    """Store statistics."""

    snapshots: int = 0
    objects: int = 0
    total_bytes: int = 0
    unique_bytes: int = 0
    dedup_pct: float = 0.0


@dataclass
class GCResult:
    """Garbage collection result."""

    removed_objects: int = 0
    freed_bytes: int = 0
