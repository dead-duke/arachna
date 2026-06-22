"""Diff computation for snapshots — orchestration, grouping, helpers."""

import hashlib
import logging
from pathlib import Path

from ...config import OutputFormat
from ...config.profile_config import ProfileConfig
from ...domain.api_types import DiffSection
from ...domain.collection.gatherer_files import _get_exclude_patterns
from ...domain.differ_stats import compute_diff_stats
from ..store.store import create_snapshot as store_create_snapshot
from ..store.store import load_snapshot
from ..store.store import update_snapshot as store_update_snapshot
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

logger = logging.getLogger("arachna.snapshot")

_MAX_SIMILARITY_SIZE = 1_048_576


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _is_binary_content(content: str) -> bool:
    return "\x00" in content


def collect_snapshot_content(profile: ProfileConfig, root: Path) -> tuple[dict, dict, dict]:
    files = _collect_snapshot_files(profile, root)
    pre_commands_data = _collect_snapshot_pre_commands(profile.to_dict(), root)
    command_data = _collect_snapshot_command(profile.to_dict(), root)
    return files, pre_commands_data, command_data


def create_snapshot(profile: ProfileConfig, name: str, root: Path) -> str:
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
    if profile is None:
        manifest = load_snapshot(snapshot_id, root=root)
        stored = manifest.get("profile", {})
        if isinstance(stored, dict):
            profile = ProfileConfig.from_dict(stored)
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


def _get_profile_from_manifest(manifest: dict) -> ProfileConfig | None:
    stored = manifest.get("profile", {})
    if isinstance(stored, dict):
        return ProfileConfig.from_dict(stored)
    return None


def _format_summary_header(stats, from_id, to_id):
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
    fmt: OutputFormat = "markdown",
    to_snapshot_id=None,
    flat=False,
    line_numbers=False,
):
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
