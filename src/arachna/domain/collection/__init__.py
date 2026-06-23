"""Collection subpackage — content gathering, command execution, mode strategies."""

from .collector import (
    _MANIFEST,
    clean_manifest,
    collect,
    load_manifest,
    save_manifest,
)
from .gatherer import (
    dry_run,
)

__all__ = [
    "_MANIFEST",
    "clean_manifest",
    "collect",
    "dry_run",
    "load_manifest",
    "save_manifest",
]
