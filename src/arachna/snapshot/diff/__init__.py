"""Diff subpackage — diff computation, structural diff, snapshot diff orchestration."""

from .differ import (
    compute_diff,
)
from .differ_structural import (
    structural_diff,
    structural_diff_for_lang,
    structural_diff_sections,
)
from .snapshot_diff import (
    collect_snapshot_content,
    create_snapshot,
    update_snapshot,
)
from .snapshot_diff import (
    compute_diff as _snapshot_compute_diff,
)
from .snapshot_diff_repo_map import (
    apply_repo_map_to_sections,
)

__all__ = [
    "_snapshot_compute_diff",
    "apply_repo_map_to_sections",
    "collect_snapshot_content",
    "compute_diff",
    "create_snapshot",
    "structural_diff",
    "structural_diff_for_lang",
    "structural_diff_sections",
    "update_snapshot",
]
