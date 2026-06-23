"""arachna is a context layer for AI workflows: snapshots, diffs, profiles. Collect once, diff forever.

Public API (stable since v5.0.0):
- arachna.collect_api.collect()
- arachna.snapshot (create_snapshot, list_snapshots, update_snapshot,
  delete_snapshot, snapshot_info, compute_diff, store_stats, store_gc)
- arachna.api_errors (ArachnaError, SnapshotNotFoundError,
  SnapshotExistsError, ProfileNotFoundError)

Semantic versioning applies to the public API. Internal modules
(domain/, config/, cli/, plugins/) may change without notice.
"""

__version__ = "5.2.2"

# Public API — stable, backward-compatible
__all__ = [
    "collect_api",
    "snapshot",
    "api_errors",
]

from .api import api_errors as api_errors
from .api import collect_api as collect_api
from .api import snapshot as snapshot
