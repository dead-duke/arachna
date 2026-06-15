# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Data classes for arachna v4.0.0 — domain layer.

All return types for public APIs and internal pipeline.
"""

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
    """Aggregate statistics for a diff result."""

    modified: int = 0
    added: int = 0
    deleted: int = 0
    renamed: int = 0
    moved: int = 0
    tokens: int = 0


@dataclass
class DiffSection:
    """A single file change within a diff."""

    type: str
    path: str
    content: str = ""
    old_path: str | None = None
    similarity: float | None = None


@dataclass
class DiffResult:
    """Complete result of a diff operation."""

    snapshot_id: str
    to_snapshot_id: str | None
    stats: DiffStats
    sections: list[DiffSection] = field(default_factory=list)


@dataclass
class PipelineMetrics:
    """Pipeline metrics for a collection operation."""

    extract_time_ms: float = 0.0
    transform_time_ms: float = 0.0
    load_time_ms: float = 0.0
    files_read: int = 0
    files_skipped: int = 0
    tokens_raw: int = 0
    tokens_compressed: int = 0
    compression_ratio: float = 1.0


@dataclass
class CollectResult:
    """Result of a collection operation."""

    parts: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    tokens: int = 0
    metrics: PipelineMetrics | None = None


@dataclass
class StoreStats:
    """Statistics about the content-addressable store."""

    snapshots: int = 0
    objects: int = 0
    total_bytes: int = 0
    unique_bytes: int = 0
    dedup_pct: float = 0.0


@dataclass
class GCResult:
    """Result of a garbage collection operation."""

    removed_objects: int = 0
    freed_bytes: int = 0
