"""Snapshot layer — snapshots, diff, store, benchmarks.

Subpackages:
- store: content-addressable store for snapshots
- diff: diff computation, structural diff, snapshot diff orchestration
- rename: rename/move detection between snapshots
"""

from .benchmarks import (
    benchmark_plugins,
    benchmark_structural_diff,
    benchmark_tiktoken,
)
from .diff import (
    apply_repo_map_to_sections,
    collect_snapshot_content,
    compute_diff,
    create_snapshot,
    structural_diff,
    structural_diff_for_lang,
    structural_diff_sections,
    update_snapshot,
)
from .store import (
    CorruptedStoreError,
    ObjectNotFoundError,
    SnapshotExistsError,
    StoreError,
    delete_snapshot,
    gc,
    list_snapshots,
    load_snapshot,
    read_object,
    rename_snapshot,
    stats,
    validate_snapshot_id,
    write_object,
)

__all__ = [
    "apply_repo_map_to_sections",
    "benchmark_plugins",
    "benchmark_structural_diff",
    "benchmark_tiktoken",
    "collect_snapshot_content",
    "compute_diff",
    "CorruptedStoreError",
    "create_snapshot",
    "delete_snapshot",
    "gc",
    "list_snapshots",
    "load_snapshot",
    "ObjectNotFoundError",
    "read_object",
    "rename_snapshot",
    "SnapshotExistsError",
    "stats",
    "StoreError",
    "structural_diff",
    "structural_diff_for_lang",
    "structural_diff_sections",
    "update_snapshot",
    "validate_snapshot_id",
    "write_object",
]
