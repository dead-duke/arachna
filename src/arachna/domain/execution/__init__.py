"""Execution subpackage — command running, content splitting, gitignore parsing."""

from .gitignore import (
    load_gitignore_patterns,
)
from .runner import (
    run_command,
    run_pre_commands,
)
from .splitter import (
    extract_signatures,
    pack_into_parts,
    split,
    split_sections,
)

__all__ = [
    "extract_signatures",
    "load_gitignore_patterns",
    "pack_into_parts",
    "run_command",
    "run_pre_commands",
    "split",
    "split_sections",
]
