# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Diff computation for Watch snapshots — v4.2.0.

Extracted from watcher.py during v4.2.0 decomposition.
Handles snapshot creation, file diff, pre_commands diff, command diff.
"""

import difflib
import fnmatch
import hashlib
import logging
import re
from pathlib import Path

from ..domain.formatter import C_LIKE_LANGS
from ..domain.gatherer_files import _get_exclude_patterns, _scan_directories
from ..domain.path_utils import validate_path
from ..domain.runner import run_command
from .differ import DiffSection, compute_diff_stats
from .differ import compute_diff as differ_compute_diff
from .store import _SHA256_PREFIX, load_snapshot, read_object, write_object
from .store import create_snapshot as store_create_snapshot
from .store import update_snapshot as store_update_snapshot
from .watcher_rename import _detect_renames_and_moves

logger = logging.getLogger("arachna.watcher")

_MAX_SIMILARITY_SIZE = 1_048_576
_COMMAND_OUTPUT_LABEL = "command output"
_PRE_LABEL_PREFIX = "pre: "


def _rel_path(absolute_path: Path, root: Path) -> str:
    """Convert absolute path to relative path from root, normalizing separators."""
    try:
        return _normalize_path(str(absolute_path.resolve().relative_to(root)))
    except ValueError:
        return _normalize_path(str(absolute_path))


def _normalize_path(path: str) -> str:
    """Normalize path separators to forward slashes and collapse duplicates."""
    path = path.replace("\\", "/")
    path = re.sub(r"/+", "/", path)
    return path


def _read_profile_files(profile: dict, root: Path) -> dict[str, str]:
    """Read files explicitly listed in profile.files, return dict[rel_path, content]."""
    result = {}
    for filepath_str in profile.get("files", []):
        fp = Path(filepath_str)
        if not fp.is_file():
            continue
        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        result[_rel_path(fp.resolve(), root)] = content
    return result


def _collect_snapshot_files(profile: dict, root: Path) -> dict[str, str]:
    """Collect files matching profile directories and patterns."""
    exclude = _get_exclude_patterns(profile, root=root)
    filepaths = _scan_directories(profile, exclude, root=root)
    files = {}
    for fp in filepaths:
        if not validate_path(fp, root):
            logger.warning("Path traversal attempt: %s", fp)
            continue
        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        files[_rel_path(fp.resolve(), root)] = content
    profile_files = _read_profile_files(profile, root)
    files.update(profile_files)
    return files


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


def _collect_snapshot_content(profile: dict, root: Path) -> tuple[dict, dict, dict]:
    """Collect all content for a snapshot: files, pre_commands output, command output."""
    files = _collect_snapshot_files(profile, root)
    pre_commands_data = _collect_snapshot_pre_commands(profile, root)
    command_data = _collect_snapshot_command(profile, root)
    return files, pre_commands_data, command_data


def create_snapshot(profile: dict, name: str, root: Path) -> str:
    """Create a named snapshot of the project state."""
    files, pre_commands_data, command_data = _collect_snapshot_content(profile, root)
    return store_create_snapshot(
        files,
        root=root,
        profile_dict=profile,
        name=name,
        pre_commands=pre_commands_data if pre_commands_data else None,
        command=command_data if command_data else None,
    )


def update_snapshot(snapshot_id: str, root: Path, profile: dict | None = None) -> str:
    """Update an existing snapshot with current project state."""
    if profile is None:
        manifest = load_snapshot(snapshot_id, root=root)
        stored = manifest.get("profile", {})
        if isinstance(stored, dict):
            profile = stored
        else:
            raise ValueError(
                f"Snapshot '{snapshot_id}' has legacy format. Provide profile explicitly."
            )
    files, pre_commands_data, command_data = _collect_snapshot_content(profile, root)
    return store_update_snapshot(
        snapshot_id,
        files,
        root=root,
        profile_dict=profile,
        pre_commands=pre_commands_data if pre_commands_data else None,
        command=command_data if command_data else None,
    )


def _get_profile_from_manifest(manifest: dict) -> dict | None:
    """Extract profile dict from snapshot manifest. Returns None if legacy format."""
    stored = manifest.get("profile", {})
    return stored if isinstance(stored, dict) else None


def _get_content_from_manifest(hash_spec: str, root: Path) -> str:
    """Read file content from content-addressable store by sha256: hash spec."""
    return read_object(hash_spec[len(_SHA256_PREFIX) :], root=root).decode("utf-8")


def _build_current_files(profile: dict, exclude: list[str], root: Path) -> dict[str, str]:
    """Build dict of current files on disk matching profile."""
    current_filepaths = _scan_directories(profile, exclude, root=root)
    current_files = {}
    for fp in current_filepaths:
        if not validate_path(fp, root):
            logger.warning("Path traversal attempt in diff: %s", fp)
            continue
        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        current_files[_rel_path(fp.resolve(), root)] = content
    profile_files = _read_profile_files(profile, root)
    for rel_path, content in profile_files.items():
        if rel_path not in current_files:
            current_files[rel_path] = content
    return current_files


def _content_hash(content: str) -> str:
    """Return SHA256 hex digest of content string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _is_binary_content(content: str) -> bool:
    """Check if content contains null bytes (binary file indicator)."""
    return "\x00" in content


def _build_deleted_added_dicts(old_files, new_files):
    """Build dicts for deleted, added, modified_old, modified_new from two file sets."""
    deleted = {}
    added = {}
    modified_old = {}
    modified_new = {}
    for path, old_content in old_files.items():
        if path in new_files:
            modified_old[path] = old_content
            modified_new[path] = new_files[path]
        else:
            deleted[path] = old_content
    for path, new_content in new_files.items():
        if path not in old_files:
            added[path] = new_content
    return deleted, added, modified_old, modified_new


def _diff_file_sets(old_files, new_files, fmt, line_numbers=False):
    """Compute diff between two file sets, including rename/move detection."""
    deleted, added, modified_old, modified_new = _build_deleted_added_dicts(old_files, new_files)
    sections = []
    rename_sections, matched_deleted, matched_added = _detect_renames_and_moves(
        deleted, added, fmt, line_numbers=line_numbers
    )
    sections.extend(rename_sections)
    for path in deleted:
        if path not in matched_deleted:
            sections.append(
                DiffSection(type="deleted", path=path, content=f"### {path}\n\n[DELETED]\n")
            )
    for path, content in added.items():
        if path not in matched_added:
            sections.append(
                DiffSection(
                    type="added",
                    path=path,
                    content=differ_compute_diff(
                        "", content, path, fmt=fmt, line_numbers=line_numbers
                    ),
                )
            )
    for path in modified_old:
        diff_output = differ_compute_diff(
            modified_old[path], modified_new[path], path, fmt=fmt, line_numbers=line_numbers
        )
        if diff_output:
            sections.append(DiffSection(type="modified", path=path, content=diff_output))
    return sections


def _diff_pre_commands_line(old_content, new_content, label):
    """Line-by-line diff for pre_commands that produce line-based output (tree, git tag)."""
    old_lines = old_content.strip().split("\n")
    new_lines = new_content.strip().split("\n")
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    parts = [f"### {label}\n"]
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
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


def _diff_files_sections(
    snapshot_id, profile, exclude, to_snapshot_id, fmt, root, line_numbers=False
):
    """Compute file diffs between snapshot(s) and current state."""
    manifest = load_snapshot(snapshot_id, root=root)
    snapshot_files = manifest.get("files", {})
    old_files = {
        path: _get_content_from_manifest(h, root=root) for path, h in snapshot_files.items()
    }
    if to_snapshot_id is not None:
        to_manifest = load_snapshot(to_snapshot_id, root=root)
        to_snapshot_files = to_manifest.get("files", {})
        new_files = {
            path: _get_content_from_manifest(h, root=root) for path, h in to_snapshot_files.items()
        }
    else:
        new_files = _build_current_files(profile, exclude, root)
        for path in list(old_files.keys()):
            if path not in new_files and not _path_matches_profile(path, profile, root):
                del old_files[path]
    return _diff_file_sets(old_files, new_files, fmt, line_numbers=line_numbers)


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
    """Group diff sections by type (renamed, moved, modified, added, deleted) with header."""
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
    streaming=False,
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
    sections.extend(_diff_pre_commands_sections(snapshot_id, profile, to_snapshot_id, fmt, root))
    sections.extend(_diff_command_section(snapshot_id, profile, to_snapshot_id, fmt, root))
    if not flat and sections:
        sections = _group_diff_sections(sections, snapshot_id, to_snapshot_id)
    return sections


def _path_matches_profile(path, profile, root):
    """Check if a file path belongs to the given profile's directories/patterns/files."""
    normalized_files = [_rel_path(Path(f), root) for f in profile.get("files", [])]
    if path in normalized_files:
        return True
    directories = profile.get("directories", [])
    patterns = profile.get("patterns", ["*"])
    path_obj = Path(path)
    for directory in directories:
        dir_path = Path(directory)
        try:
            path_obj.relative_to(dir_path)
        except ValueError:
            continue
        for pat in patterns:
            if fnmatch.fnmatch(path_obj.name, pat):
                return True
    return False


def _get_snapshot_files(snapshot_id, to_snapshot_id, root):
    """Get file dicts from snapshot(s)."""
    manifest = load_snapshot(snapshot_id, root=root)
    snapshot_files = manifest.get("files", {})
    to_files = None
    if to_snapshot_id:
        to_manifest = load_snapshot(to_snapshot_id, root=root)
        to_files = to_manifest.get("files", {})
    return snapshot_files, to_files


def _parse_blocks_for_lang(content, lang, parser):
    """Parse content into blocks for the given language."""
    if content is None or parser is None:
        return None
    if lang in C_LIKE_LANGS or lang == "gdscript":
        return parser(content, lang)
    return parser(content)


def _repo_map_modified_section(s, lang, parser, snapshot_files, to_files, root):
    """Apply repo-map transformation to a modified section."""
    old_content = _read_file_from_store(s.path, snapshot_files, root)
    new_content = (
        _read_file_from_disk(root / s.path, root)
        if to_files is None
        else _read_file_from_store(s.path, to_files, root)
    )
    old_blocks = _parse_blocks_for_lang(old_content, lang, parser)
    new_blocks = _parse_blocks_for_lang(new_content, lang, parser)
    if old_blocks is not None and new_blocks is not None:
        s.content = _format_repo_map_diff(s.path, old_blocks, new_blocks)


def _repo_map_added_section(s, lang, parser, to_files, root):
    """Apply repo-map transformation to an added section."""
    new_content = (
        _read_file_from_disk(root / s.path, root)
        if to_files is None
        else _read_file_from_store(s.path, to_files, root)
    )
    blocks = _parse_blocks_for_lang(new_content, lang, parser)
    if blocks is not None:
        s.content = _format_repo_map_added(s.path, blocks)


def _repo_map_deleted_section(s, lang, parser, snapshot_files, root):
    """Apply repo-map transformation to a deleted section."""
    old_content = _read_file_from_store(s.path, snapshot_files, root)
    blocks = _parse_blocks_for_lang(old_content, lang, parser)
    if blocks is not None:
        sig_lines = [f"  {sig}" for sig, _body in blocks.values()]
        if sig_lines:
            s.content = (
                f"### {s.path}\n\n[DELETED]\n\nRemoved signatures:\n" + "\n".join(sig_lines) + "\n"
            )


def _apply_repo_map_to_sections(sections, snapshot_id, to_snapshot_id, profile, root):
    """Apply repo-map transformation to diff sections (signatures only)."""
    from ..domain.formatter import lang_for_path
    from ..domain.language_dispatch import get_block_parser

    snapshot_files, to_files = _get_snapshot_files(snapshot_id, to_snapshot_id, root)
    result = []
    for s in sections:
        if s.type in ("header",) or not s.path:
            result.append(s)
            continue
        lang = lang_for_path(Path(s.path))
        parser = get_block_parser(lang)
        if s.type == "modified":
            _repo_map_modified_section(s, lang, parser, snapshot_files, to_files, root)
        elif s.type == "added":
            _repo_map_added_section(s, lang, parser, to_files, root)
        elif s.type == "deleted":
            _repo_map_deleted_section(s, lang, parser, snapshot_files, root)
        result.append(s)
    return result


def _read_file_from_store(path, files, root):
    """Read file content from content-addressable store by path lookup."""
    for fpath, hash_spec in files.items():
        if fpath == path:
            try:
                return read_object(hash_spec[len(_SHA256_PREFIX) :], root=root).decode("utf-8")
            except Exception:
                return None
    return None


def _read_file_from_disk(path, root=None):
    """Read file content from disk with error handling."""
    fp = Path(path)
    if root is not None and not validate_path(fp, root):
        logger.warning("Path traversal attempt in repo-map: %s", fp)
        return None
    if not fp.is_file():
        return None
    try:
        return fp.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _format_repo_map_entry(name, old, new, parts):
    """Format a single repo-map diff entry for one named block."""
    import hashlib

    if old is None and new is not None:
        sig, _body = new
        parts.append(f"+ {sig}\n")
    elif old is not None and new is None:
        sig, _body = old
        parts.append(f"- {sig}\n")
    elif old is not None and new is not None:
        old_sig, old_body = old
        new_sig, new_body = new
        sig_changed = old_sig != new_sig
        body_changed = (
            hashlib.sha256(old_body.encode()).hexdigest()
            != hashlib.sha256(new_body.encode()).hexdigest()
        )
        if sig_changed:
            parts.append(f"~ {old_sig}\n  -> {new_sig}\n")
        elif body_changed:
            parts.append(f"  {old_sig}  (body changed)\n")


def _format_repo_map_diff(path, old_blocks, new_blocks):
    """Format repo-map diff output showing added/removed/modified signatures."""
    all_names = set(old_blocks.keys()) | set(new_blocks.keys())
    parts = [f"### {path}\n"]
    for name in sorted(all_names):
        old = old_blocks.get(name)
        new = new_blocks.get(name)
        _format_repo_map_entry(name, old, new, parts)
    return "".join(parts) if len(parts) > 1 else ""


def _format_repo_map_added(path, blocks):
    """Format repo-map output for added files (all signatures)."""
    parts = [f"### {path}\n"]
    for _name, (sig, _body) in blocks.items():
        parts.append(f"+ {sig}\n")
    return "".join(parts) if len(parts) > 1 else ""
