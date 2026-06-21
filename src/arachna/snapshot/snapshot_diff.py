# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Diff computation for snapshots — orchestration, grouping, helpers."""

import hashlib
import logging
from pathlib import Path

from ..config.profile_config import ProfileConfig
from ..domain.api_types import DiffSection
from ..domain.differ_stats import compute_diff_stats
from ..domain.gatherer_files import _get_exclude_patterns
from .snapshot_diff_commands import (
    _collect_snapshot_command,
    _collect_snapshot_pre_commands,
    _diff_command_section,
    _diff_pre_commands_sections,
)
from .snapshot_diff_files import (
    _collect_snapshot_files,
    _diff_files_sections,
)
from .store import create_snapshot as store_create_snapshot
from .store import load_snapshot
from .store import update_snapshot as store_update_snapshot

logger = logging.getLogger("arachna.snapshot")

_MAX_SIMILARITY_SIZE = 1_048_576


def _content_hash(content: str) -> str:
    """Return SHA256 hex digest of content string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _is_binary_content(content: str) -> bool:
    """Check if content contains null bytes (binary file indicator)."""
    return "\x00" in content


def collect_snapshot_content(profile: ProfileConfig, root: Path) -> tuple[dict, dict, dict]:
    """Collect all content for a snapshot: files, pre_commands output, command output."""
    files = _collect_snapshot_files(profile, root)
    pre_commands_data = _collect_snapshot_pre_commands(profile.to_dict(), root)
    command_data = _collect_snapshot_command(profile.to_dict(), root)
    return files, pre_commands_data, command_data


def create_snapshot(profile: ProfileConfig, name: str, root: Path) -> str:
    """Create a named snapshot of the project state."""
    files, pre_commands_data, command_data = collect_snapshot_content(profile, root)
    return store_create_snapshot(
        files,
        root=root,
        profile_dict=profile.to_dict(),
        name=name,
        pre_commands=pre_commands_data if pre_commands_data else None,
        command=command_data if command_data else None,
    )


def update_snapshot(snapshot_id: str, root: Path, profile: ProfileConfig | None = None) -> str:
    """Update an existing snapshot with current project state."""
    if profile is None:
        manifest = load_snapshot(snapshot_id, root=root)
        stored = manifest.get("profile", {})
        if isinstance(stored, dict):
            profile = _dict_to_profile_config(stored)
        else:
            raise ValueError(
                f"Snapshot '{snapshot_id}' has legacy format. Provide profile explicitly."
            )
    files, pre_commands_data, command_data = collect_snapshot_content(profile, root)
    return store_update_snapshot(
        snapshot_id,
        files,
        root=root,
        profile_dict=profile.to_dict(),
        pre_commands=pre_commands_data if pre_commands_data else None,
        command=command_data if command_data else None,
    )


def _dict_to_profile_config(d: dict) -> ProfileConfig:
    defaults = ProfileConfig()
    return ProfileConfig(
        name_template=d.get("name_template", defaults.name_template),
        title_template=d.get("title_template", defaults.title_template),
        max_tokens=d.get("max_tokens", defaults.max_tokens),
        split_mode=d.get("split_mode", defaults.split_mode),
        directories=d.get("directories", defaults.directories),
        patterns=d.get("patterns", defaults.patterns),
        files=d.get("files", defaults.files),
        exclude_patterns=d.get("exclude_patterns", defaults.exclude_patterns),
        pre_commands=d.get("pre_commands", defaults.pre_commands),
        post_commands=d.get("post_commands", defaults.post_commands),
        command=d.get("command"),
        section_format=d.get("section_format", defaults.section_format),
        compress=d.get("compress", defaults.compress),
        include_binary=d.get("include_binary", defaults.include_binary),
        binary_extensions=d.get("binary_extensions"),
        binary_max_mb=d.get("binary_max_mb", defaults.binary_max_mb),
        tokenizer=d.get("tokenizer", defaults.tokenizer),
        chars_per_token=d.get("chars_per_token"),
        line_numbers=d.get("line_numbers", defaults.line_numbers),
        extends=d.get("extends"),
        remote=d.get("remote", defaults.remote),
        use_gitignore=d.get("use_gitignore", defaults.use_gitignore),
        split_marker=d.get("split_marker", defaults.split_marker),
    )


def _get_profile_from_manifest(manifest: dict) -> ProfileConfig | None:
    """Extract profile dict from snapshot manifest. Returns None if legacy format."""
    stored = manifest.get("profile", {})
    if isinstance(stored, dict):
        return _dict_to_profile_config(stored)
    return None


def _format_summary_header(stats, from_id, to_id):
    """Format diff summary header with change counts."""
    parts = []
    if stats["renamed"]:
        parts.append(f"{stats['renamed']} renamed")
    if stats["moved"]:
        parts.append(f"{stats['moved']} moved")
    if stats["modified"]:
        parts.append(f"{stats['modified']} modified")
    if stats["added"]:
        parts.append(f"{stats['added']} added")
    if stats["deleted"]:
        parts.append(f"{stats['deleted']} deleted")
    if not parts:
        return "## No changes\n\n"
    to_label = to_id if to_id else "current"
    return f"## Changes from {from_id} to {to_label} ({', '.join(parts)})\n\n"


def _group_diff_sections(sections, from_id, to_id):
    """Group diff sections by type with header."""
    if not sections:
        return sections
    stats = compute_diff_stats(sections)
    header = _format_summary_header(stats, from_id, to_id)
    grouped = {"renamed": [], "moved": [], "modified": [], "added": [], "deleted": []}
    for s in sections:
        if s.type in grouped:
            grouped[s.type].append(s)
        else:
            grouped["modified"].append(s)
    result = [DiffSection(type="header", path="", content=header)]
    section_headers = {
        "renamed": "### Renamed\n",
        "moved": "### Moved\n",
        "modified": "### Modified\n",
        "added": "### Added\n",
        "deleted": "### Deleted\n",
    }
    for group_type in ["renamed", "moved", "modified", "added", "deleted"]:
        group = grouped[group_type]
        if not group:
            continue
        result.append(DiffSection(type=group_type, path="", content=section_headers[group_type]))
        result.extend(group)
    return result


def compute_diff(
    snapshot_id,
    profile,
    root,
    fmt="markdown",
    to_snapshot_id=None,
    flat=False,
    line_numbers=False,
):
    """Compute diff between snapshot and current state or between two snapshots."""
    manifest = load_snapshot(snapshot_id, root=root)
    if profile is None:
        profile = _get_profile_from_manifest(manifest)
        if profile is None:
            raise ValueError(f"Snapshot '{snapshot_id}' has legacy format. Use --profile.")
    exclude = _get_exclude_patterns(profile, root=root)
    sections = _diff_files_sections(
        snapshot_id, profile, exclude, to_snapshot_id, fmt, root, line_numbers=line_numbers
    )
    sections.extend(
        _diff_pre_commands_sections(snapshot_id, profile.to_dict(), to_snapshot_id, fmt, root)
    )
    sections.extend(
        _diff_command_section(snapshot_id, profile.to_dict(), to_snapshot_id, fmt, root)
    )
    if not flat and sections:
        sections = _group_diff_sections(sections, snapshot_id, to_snapshot_id)
    return sections
