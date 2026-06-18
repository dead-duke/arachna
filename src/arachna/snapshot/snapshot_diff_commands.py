# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Snapshot command and pre_command diff — execution, output diff strategies."""

import difflib
import logging
from pathlib import Path

from ..domain.api_types import DiffSection
from ..domain.runner import run_command
from .differ import compute_diff as differ_compute_diff
from .snapshot_diff_files import _get_content_from_manifest
from .store import _SHA256_PREFIX, load_snapshot, write_object

logger = logging.getLogger("arachna.snapshot")

_COMMAND_OUTPUT_LABEL = "command output"
_PRE_LABEL_PREFIX = "pre: "


def _collect_snapshot_pre_commands(profile: dict, root: Path) -> dict[str, str]:
    """Execute pre_commands and store outputs."""
    pre_commands_data = {}
    for cmd in profile.get("pre_commands", []):
        output = run_command(cmd, root=root, allow_file_args=True)
        if output.strip():
            label = cmd if len(cmd) <= 50 else cmd[:47] + "..."
            obj_hash = write_object(output.encode("utf-8"), root=root)
            pre_commands_data[f"{_PRE_LABEL_PREFIX}{label}"] = f"{_SHA256_PREFIX}{obj_hash}"
        else:
            logger.warning("pre_command produced no output: %s", cmd[:80])
    return pre_commands_data


def _collect_snapshot_command(profile: dict, root: Path) -> dict[str, str]:
    """Execute command profile and store output."""
    command_data = {}
    cmd = profile.get("command")
    if cmd:
        output = run_command(cmd, root=root, allow_file_args=True)
        if output.strip():
            obj_hash = write_object(output.encode("utf-8"), root=root)
            command_data[_COMMAND_OUTPUT_LABEL] = f"{_SHA256_PREFIX}{obj_hash}"
        else:
            logger.warning("command produced no output: %s", cmd[:80])
    return command_data


def _append_diff_lines(parts, tag, old_lines, i1, i2, new_lines, j1, j2):
    """Append diff lines for one opcode to the parts list."""
    if tag == "delete":
        for line in old_lines[i1:i2]:
            parts.append(f"- {line}\n")
    elif tag == "insert":
        for line in new_lines[j1:j2]:
            parts.append(f"+ {line}\n")
    elif tag == "replace":
        for line in old_lines[i1:i2]:
            parts.append(f"- {line}\n")
        for line in new_lines[j1:j2]:
            parts.append(f"+ {line}\n")


def _diff_pre_commands_line(old_content, new_content, label):
    """Line-by-line diff for pre_commands that produce line-based output (tree, git tag)."""
    old_lines = old_content.strip().split("\n")
    new_lines = new_content.strip().split("\n")
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    parts = [f"### {label}\n"]
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        _append_diff_lines(parts, tag, old_lines, i1, i2, new_lines, j1, j2)
    return "".join(parts) if len(parts) > 1 else ""


def _diff_pre_commands_marker(old_content, new_content, label, marker, fmt):
    """Section-by-section diff for pre_commands with marker separators (git log)."""
    from ..domain.splitter import _split_to_sections

    old_sections = _split_to_sections(old_content, marker)
    new_sections = _split_to_sections(new_content, marker)
    result_parts = []
    min_len = min(len(old_sections), len(new_sections))
    for i in range(min_len):
        old_sec = old_sections[i]
        new_sec = new_sections[i]
        if old_sec != new_sec:
            diff = differ_compute_diff(old_sec, new_sec, f"{label} section {i + 1}", fmt=fmt)
            if diff.strip():
                result_parts.append(diff)
    if len(new_sections) > len(old_sections):
        for i in range(len(old_sections), len(new_sections)):
            result_parts.append(
                differ_compute_diff("", new_sections[i], f"{label} section {i + 1}", fmt=fmt)
            )
    if len(old_sections) > len(new_sections):
        for i in range(len(new_sections), len(old_sections)):
            result_parts.append(f"### {label} section {i + 1}\n\n[DELETED]\n")
    return "\n".join(result_parts)


def _diff_pre_commands_structural(old_content, new_content, label, cmd, fmt):
    """Dispatch pre_command diff to line-based or marker-based based on command type."""
    cmd_basename = Path(cmd.strip().split()[0]).name if cmd.strip() else ""
    if cmd_basename == "tree" or (cmd_basename == "git" and "tag" in cmd):
        return _diff_pre_commands_line(old_content, new_content, label)
    if cmd_basename == "git" and "log" in cmd:
        return _diff_pre_commands_marker(old_content, new_content, label, "\n=== COMMIT:", fmt)
    return differ_compute_diff(old_content, new_content, label, fmt=fmt)


def _build_pre_command_map(profile: dict) -> dict[str, str]:
    """Build mapping from pre_command label to original command."""
    cmd_map = {}
    for cmd in profile.get("pre_commands", []):
        label = f"{_PRE_LABEL_PREFIX}{cmd if len(cmd) <= 50 else cmd[:47] + '...'}"
        cmd_map[label] = cmd
    return cmd_map


def _build_current_pre_commands(profile: dict, root: Path) -> dict[str, str]:
    """Execute current pre_commands and return label -> output mapping."""
    current_pre = {}
    for cmd in profile.get("pre_commands", []):
        output = run_command(cmd, root=root, allow_file_args=True)
        if output.strip():
            label = f"{_PRE_LABEL_PREFIX}{cmd if len(cmd) <= 50 else cmd[:47] + '...'}"
            current_pre[label] = output
    return current_pre


def _diff_existing_pre_command(label, old_content, current_pre, cmd_map, fmt):
    """Diff a pre_command that existed in the snapshot."""
    if label in current_pre:
        cmd = cmd_map.get(label, "")
        diff_output = (
            _diff_pre_commands_structural(old_content, current_pre[label], label, cmd, fmt)
            if cmd
            else differ_compute_diff(old_content, current_pre[label], label, fmt=fmt)
        )
        if diff_output:
            return DiffSection(type="modified", path=label, content=diff_output)
    else:
        removed_lines = "\n".join(f"- {line}" for line in old_content.strip().split("\n"))
        return DiffSection(
            type="deleted",
            path=label,
            content=f"### {label}\n\n[DELETED]\n\n{removed_lines}\n",
        )
    return None


def _diff_new_pre_command(label, cmd_map, fmt):
    """Create an 'added' section for a new pre_command."""
    cmd = cmd_map.get(label, "")
    diff_output = (
        _diff_pre_commands_structural("", "", label, cmd, fmt)
        if cmd
        else differ_compute_diff("", "", label, fmt=fmt)
    )
    return DiffSection(type="added", path=label, content=diff_output)


def _diff_pre_commands_sections(snapshot_id, profile, to_snapshot_id, fmt, root):
    """Compute pre_commands diffs between snapshot(s) and current state."""
    manifest = load_snapshot(snapshot_id, root=root)
    snapshot_pre = manifest.get("pre_commands", {})
    current_pre = {}
    if to_snapshot_id is not None:
        to_manifest = load_snapshot(to_snapshot_id, root=root)
        snapshot_to_pre = to_manifest.get("pre_commands", {})
        for label, hash_spec in snapshot_to_pre.items():
            current_pre[label] = _get_content_from_manifest(hash_spec, root=root)
    else:
        current_pre = _build_current_pre_commands(profile, root)
    cmd_map = _build_pre_command_map(profile)
    sections = []
    for label, hash_spec in snapshot_pre.items():
        old_content = _get_content_from_manifest(hash_spec, root=root)
        section = _diff_existing_pre_command(label, old_content, current_pre, cmd_map, fmt)
        if section:
            sections.append(section)
    for label in current_pre:
        if label not in snapshot_pre:
            sections.append(_diff_new_pre_command(label, cmd_map, fmt))
    return sections


def _get_current_cmd_output(to_snapshot_id, profile, root):
    """Get current command output from either target snapshot or current profile."""
    if to_snapshot_id is not None:
        to_manifest = load_snapshot(to_snapshot_id, root=root)
        snapshot_to_cmd = to_manifest.get("command", {})
        for _label, hash_spec in snapshot_to_cmd.items():
            return _get_content_from_manifest(hash_spec, root=root)
        return ""
    cmd = profile.get("command")
    if cmd:
        output = run_command(cmd, root=root, allow_file_args=True)
        if output.strip():
            return output
    return ""


def _diff_cmd_modified(snapshot_cmd, current_cmd_output, fmt, root):
    """Build modified sections for command diff."""
    sections = []
    for label, hash_spec in snapshot_cmd.items():
        old_content = _get_content_from_manifest(hash_spec, root=root)
        diff_output = differ_compute_diff(old_content, current_cmd_output, label, fmt=fmt)
        if diff_output:
            sections.append(DiffSection(type="modified", path=label, content=diff_output))
    return sections


def _diff_cmd_deleted(snapshot_cmd, root):
    """Build deleted sections for command diff."""
    sections = []
    for label, hash_spec in snapshot_cmd.items():
        old_content = _get_content_from_manifest(hash_spec, root=root)
        removed_lines = "\n".join(f"- {line}" for line in old_content.strip().split("\n"))
        sections.append(
            DiffSection(
                type="deleted",
                path=label,
                content=f"### {label}\n\n[DELETED]\n\n{removed_lines}\n",
            )
        )
    return sections


def _diff_cmd_added(current_cmd_output, fmt):
    """Build added section for command diff."""
    diff_output = differ_compute_diff("", current_cmd_output, _COMMAND_OUTPUT_LABEL, fmt=fmt)
    return [DiffSection(type="added", path=_COMMAND_OUTPUT_LABEL, content=diff_output)]


def _diff_command_section(snapshot_id, profile, to_snapshot_id, fmt, root):
    """Compute command output diff between snapshot(s) and current state."""
    manifest = load_snapshot(snapshot_id, root=root)
    snapshot_cmd = manifest.get("command", {})
    current_cmd_output = _get_current_cmd_output(to_snapshot_id, profile, root)
    has_snapshot = bool(snapshot_cmd)
    has_current = bool(current_cmd_output)
    if has_snapshot and has_current:
        return _diff_cmd_modified(snapshot_cmd, current_cmd_output, fmt, root)
    elif has_snapshot and not has_current:
        return _diff_cmd_deleted(snapshot_cmd, root)
    elif not has_snapshot and has_current:
        return _diff_cmd_added(current_cmd_output, fmt)
    return []
