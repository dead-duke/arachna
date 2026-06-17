# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Backward-compat re-exports for gatherer_core.

DEPRECATED: Use gatherer_files and gatherer_commands directly.
"""

from .gatherer_commands import _collect_pre_commands, gather_command, gather_files
from .gatherer_files import (
    _collect_directory_sections,
    _collect_file_sections,
    _collect_named_sections,
    _format_file_list,
    _format_one_file,
    _get_exclude_patterns,
    _get_profile_files,
    _print_compress_stats,
    _scan_directories,
)

__all__ = [
    "_collect_directory_sections",
    "_collect_file_sections",
    "_collect_named_sections",
    "_collect_pre_commands",
    "_format_file_list",
    "_format_one_file",
    "_get_exclude_patterns",
    "_get_profile_files",
    "_print_compress_stats",
    "_scan_directories",
    "gather_command",
    "gather_files",
]
