# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Watcher — orchestration layer between CLI, store, and differ.

v4.2.0: Split into watcher_diff.py + watcher_rename.py.
This module re-exports for backward compatibility.
"""

from .watcher_diff import (
    _apply_repo_map_to_sections,
    _build_current_files,
    _collect_snapshot_content,
    _content_hash,
    _diff_command_section,
    _diff_file_sets,
    _diff_files_sections,
    _diff_pre_commands_line,
    _diff_pre_commands_marker,
    _diff_pre_commands_sections,
    _diff_pre_commands_structural,
    _format_repo_map_added,
    _format_repo_map_diff,
    _format_summary_header,
    _get_content_from_manifest,
    _get_profile_from_manifest,
    _group_diff_sections,
    _is_binary_content,
    _normalize_path,
    _path_matches_profile,
    _read_file_from_disk,
    _read_file_from_store,
    _read_profile_files,
    _rel_path,
    compute_diff,
    create_snapshot,
    update_snapshot,
)
from .watcher_rename import (
    _detect_renames_and_moves,
    _match_exact_renames,
    _match_similar_renames,
)

__all__ = [
    "_apply_repo_map_to_sections",
    "_build_current_files",
    "_collect_snapshot_content",
    "_content_hash",
    "_detect_renames_and_moves",
    "_diff_command_section",
    "_diff_file_sets",
    "_diff_files_sections",
    "_diff_pre_commands_line",
    "_diff_pre_commands_marker",
    "_diff_pre_commands_sections",
    "_diff_pre_commands_structural",
    "_format_repo_map_added",
    "_format_repo_map_diff",
    "_format_summary_header",
    "_get_content_from_manifest",
    "_get_profile_from_manifest",
    "_group_diff_sections",
    "_is_binary_content",
    "_match_exact_renames",
    "_match_similar_renames",
    "_normalize_path",
    "_path_matches_profile",
    "_read_file_from_disk",
    "_read_file_from_store",
    "_read_profile_files",
    "_rel_path",
    "compute_diff",
    "create_snapshot",
    "update_snapshot",
]
