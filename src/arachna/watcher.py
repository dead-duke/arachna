"""Watcher — orchestration layer between CLI, store, and differ.

Walks project files, creates snapshots, and computes diffs
against previously stored snapshots.
"""

import difflib
import fnmatch
import hashlib
from pathlib import Path

from .differ import DiffSection, compute_diff_stats
from .differ import compute_diff as differ_compute_diff
from .gatherer import _get_exclude_patterns, _scan_directories
from .runner import run_command
from .store import create_snapshot as store_create_snapshot
from .store import load_snapshot, read_object, write_object
from .store import update_snapshot as store_update_snapshot


def _normalize_path(path: str) -> str:
    """Convert Windows backslashes to forward slashes for cross-platform consistency."""
    return path.replace("\\", "/")


def _read_profile_files(profile: dict) -> dict[str, str]:
    """Read explicitly listed files from profile.

    Returns {normalized_path: content} dict.
    Skips files that don't exist or can't be read.
    """
    result = {}
    cwd = Path.cwd()
    for filepath_str in profile.get("files", []):
        fp = Path(filepath_str)
        if not fp.is_file():
            continue
        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            rel_path = _normalize_path(str(fp.relative_to(cwd)))
        except ValueError:
            rel_path = _normalize_path(str(fp))
        result[rel_path] = content
    return result


def _collect_snapshot_content(profile: dict) -> tuple[dict, dict, dict]:
    """Collect files, pre_commands, and command output for a snapshot.

    Returns (files_dict, pre_commands_data, command_data).
    """
    exclude = _get_exclude_patterns(profile)
    filepaths = _scan_directories(profile, exclude)

    files = {}
    for fp in filepaths:
        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            rel_path = _normalize_path(str(fp.relative_to(Path.cwd())))
        except ValueError:
            rel_path = _normalize_path(str(fp))
        files[rel_path] = content

    profile_files = _read_profile_files(profile)
    files.update(profile_files)

    pre_commands_data = {}
    for cmd in profile.get("pre_commands", []):
        output = run_command(cmd)
        if output.strip():
            label = cmd if len(cmd) <= 50 else cmd[:47] + "..."
            obj_hash = write_object(output.encode("utf-8"))
            pre_commands_data[f"pre: {label}"] = f"sha256:{obj_hash}"

    command_data = {}
    cmd = profile.get("command")
    if cmd:
        output = run_command(cmd)
        if output.strip():
            obj_hash = write_object(output.encode("utf-8"))
            command_data["command output"] = f"sha256:{obj_hash}"

    return files, pre_commands_data, command_data


def create_snapshot(profile: dict, name: str) -> str:
    """Walk all files in profile and create a snapshot.

    Stores full profile dict in manifest for later use by --diff
    without requiring --profile flag.

    Args:
        profile: profile dict (same format as .arachna.json profiles).
        name: required human-readable name for the snapshot.

    Returns:
        Snapshot ID (same as name).

    Raises:
        store_errors.SnapshotExistsError: if snapshot with this name exists.
    """
    files, pre_commands_data, command_data = _collect_snapshot_content(profile)

    return store_create_snapshot(
        files,
        profile_dict=profile,
        name=name,
        pre_commands=pre_commands_data if pre_commands_data else None,
        command=command_data if command_data else None,
    )


def update_snapshot(snapshot_id: str, profile: dict | None = None) -> str:
    """Update an existing snapshot with current content.

    If profile is given, updates stored profile. Otherwise uses
    existing profile from manifest.

    Args:
        snapshot_id: ID of the snapshot to update.
        profile: optional new profile dict. If None, uses existing.

    Returns:
        Snapshot ID (same as input).

    Raises:
        store_errors.ObjectNotFoundError: if snapshot doesn't exist.
    """
    if profile is None:
        manifest = load_snapshot(snapshot_id)
        stored = manifest.get("profile", {})
        if isinstance(stored, dict):
            profile = stored
        else:
            raise ValueError(
                f"Snapshot '{snapshot_id}' has legacy format (profile is a string). "
                f"Use --profile to specify a profile."
            )

    files, pre_commands_data, command_data = _collect_snapshot_content(profile)

    return store_update_snapshot(
        snapshot_id,
        files,
        profile_dict=profile,
        pre_commands=pre_commands_data if pre_commands_data else None,
        command=command_data if command_data else None,
    )


def _get_profile_from_manifest(manifest: dict) -> dict | None:
    """Extract profile dict from manifest.

    Returns dict if manifest has profile as dict, None if legacy string format.
    """
    stored = manifest.get("profile", {})
    if isinstance(stored, dict):
        return stored
    return None


def _get_content_from_manifest(
    path: str,
    hash_spec: str,
) -> str:
    """Read file content from store by hash spec.

    Args:
        path: file path (for error messages).
        hash_spec: "sha256:abcdef..." string.

    Returns:
        Decoded file content as string.
    """
    obj_hash = hash_spec[7:]  # strip "sha256:"
    return read_object(obj_hash).decode("utf-8")


def _build_current_files(
    profile: dict,
    exclude: list[str],
) -> dict[str, str]:
    """Build dict of current files from disk.

    Returns {normalized_path: content}.
    """
    current_filepaths = _scan_directories(profile, exclude)

    current_files = {}
    for fp in current_filepaths:
        try:
            rel_path = _normalize_path(str(fp.relative_to(Path.cwd())))
        except ValueError:
            rel_path = _normalize_path(str(fp))
        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        current_files[rel_path] = content

    profile_files = _read_profile_files(profile)
    for rel_path, content in profile_files.items():
        if rel_path not in current_files:
            current_files[rel_path] = content

    return current_files


def _content_hash(content: str) -> str:
    """Compute SHA256 hash of content string for exact match detection."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _is_binary_content(content: str) -> bool:
    """Check if content appears to be binary (contains null bytes)."""
    return "\x00" in content


def _detect_renames_and_moves(
    deleted: dict[str, str],
    added: dict[str, str],
    fmt: str,
) -> tuple[list[DiffSection], set[str], set[str]]:
    """Detect renames and moves between deleted and added files.

    Algorithm:
    1. Exact match by content hash:
       - Same content, different filename → RENAMED (exact)
       - Same content, different directory → MOVED (exact)
       - Same content, different name AND directory → MOVED AND RENAMED
       - Same path → skip (not a rename/move)
       - Multiple files with same hash → ambiguous, skip all
    2. Similarity match (SequenceMatcher > 0.7):
       - Different filename → RENAMED AND MODIFIED
       - Different directory → MOVED AND MODIFIED
    3. Edge cases:
       - Binary files → hash comparison only
       - ratio <= 0.7 → separate delete + add

    Returns (rename_sections, matched_deleted, matched_added).
    """
    rename_sections = []
    matched_deleted: set[str] = set()
    matched_added: set[str] = set()

    deleted_by_hash: dict[str, list[str]] = {}
    for path, content in deleted.items():
        ch = _content_hash(content)
        deleted_by_hash.setdefault(ch, []).append(path)

    added_by_hash: dict[str, list[str]] = {}
    for path, content in added.items():
        ch = _content_hash(content)
        added_by_hash.setdefault(ch, []).append(path)

    # Phase 1: exact hash matches
    for ch, del_paths in list(deleted_by_hash.items()):
        if ch not in added_by_hash:
            continue
        add_paths = added_by_hash[ch]

        if len(del_paths) == 1 and len(add_paths) == 1:
            old_path = del_paths[0]
            new_path = add_paths[0]

            if old_path == new_path:
                matched_deleted.add(old_path)
                matched_added.add(new_path)
                continue

            old_dir = str(Path(old_path).parent)
            new_dir = str(Path(new_path).parent)
            old_name = Path(old_path).name
            new_name = Path(new_path).name

            if old_dir == new_dir and old_name != new_name:
                rename_sections.append(
                    DiffSection(
                        type="renamed",
                        path=new_path,
                        old_path=old_path,
                        similarity=1.0,
                        content=f"RENAMED: {old_path} → {new_path}\n",
                    )
                )
            elif old_dir != new_dir and old_name == new_name:
                rename_sections.append(
                    DiffSection(
                        type="moved",
                        path=new_path,
                        old_path=old_path,
                        similarity=1.0,
                        content=f"MOVED: {old_path} → {new_path}\n",
                    )
                )
            else:
                rename_sections.append(
                    DiffSection(
                        type="renamed",
                        path=new_path,
                        old_path=old_path,
                        similarity=1.0,
                        content=f"MOVED AND RENAMED: {old_path} → {new_path}\n",
                    )
                )

            matched_deleted.add(old_path)
            matched_added.add(new_path)
        else:
            for p in del_paths:
                matched_deleted.add(p)
            for p in add_paths:
                matched_added.add(p)

    # Phase 2: similarity detection
    remaining_deleted = {p: c for p, c in deleted.items() if p not in matched_deleted}
    remaining_added = {p: c for p, c in added.items() if p not in matched_added}

    for del_path, del_content in remaining_deleted.items():
        if _is_binary_content(del_content):
            continue

        for add_path, add_content in list(remaining_added.items()):
            if _is_binary_content(add_content):
                continue

            ratio = difflib.SequenceMatcher(None, del_content, add_content).ratio()
            if ratio > 0.7:
                old_dir = str(Path(del_path).parent)
                new_dir = str(Path(add_path).parent)
                old_name = Path(del_path).name
                new_name = Path(add_path).name

                if old_dir == new_dir:
                    action = f"RENAMED: {del_path} → {add_path} ({ratio:.0%} similar)"
                    section_type = "renamed"
                elif old_name == new_name:
                    action = f"MOVED: {del_path} → {add_path} ({ratio:.0%} similar)"
                    section_type = "moved"
                else:
                    action = f"MOVED AND RENAMED: {del_path} → {add_path} ({ratio:.0%} similar)"
                    section_type = "renamed"

                diff_output = differ_compute_diff(del_content, add_content, add_path, fmt=fmt)
                content = f"{action}\n\n{diff_output}" if diff_output else f"{action}\n"

                rename_sections.append(
                    DiffSection(
                        type=section_type,
                        path=add_path,
                        old_path=del_path,
                        similarity=ratio,
                        content=content,
                    )
                )
                matched_deleted.add(del_path)
                matched_added.add(add_path)
                del remaining_added[add_path]
                break

    return rename_sections, matched_deleted, matched_added


def _diff_file_sets(
    old_files: dict[str, str],
    new_files: dict[str, str],
    fmt: str,
) -> list[DiffSection]:
    """Compare two file sets and return DiffSections with rename/move detection.

    Args:
        old_files: {path: content} from snapshot A.
        new_files: {path: content} from snapshot B or current state.
        fmt: "markdown" or "xml".

    Returns:
        List of DiffSection objects (flat, ungrouped).
    """
    sections: list[DiffSection] = []

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

    rename_sections, matched_deleted, matched_added = _detect_renames_and_moves(deleted, added, fmt)
    sections.extend(rename_sections)

    for path in deleted:
        if path not in matched_deleted:
            sections.append(
                DiffSection(type="deleted", path=path, content=f"### {path}\n\n[DELETED]\n")
            )

    for path, content in added.items():
        if path not in matched_added:
            diff_output = differ_compute_diff("", content, path, fmt=fmt)
            sections.append(DiffSection(type="added", path=path, content=diff_output))

    for path in modified_old:
        diff_output = differ_compute_diff(modified_old[path], modified_new[path], path, fmt=fmt)
        if diff_output:
            sections.append(DiffSection(type="modified", path=path, content=diff_output))

    return sections


def _format_summary_header(stats: dict, from_id: str, to_id: str | None) -> str:
    """Generate summary header for grouped diff output.

    Args:
        stats: dict from compute_diff_stats with renamed/moved/modified/added/deleted counts.
        from_id: source snapshot ID.
        to_id: target snapshot ID or None for current files.

    Returns:
        Summary header string.
    """
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


def _group_diff_sections(
    sections: list[DiffSection], from_id: str, to_id: str | None
) -> list[DiffSection]:
    """Group flat DiffSections by type with headers.

    Order: renamed, moved, modified, added, deleted.
    Adds a summary header at the beginning.

    Args:
        sections: flat list of DiffSections.
        from_id: source snapshot ID.
        to_id: target snapshot ID or None.

    Returns:
        Grouped list with header sections.
    """
    if not sections:
        return sections

    stats = compute_diff_stats(sections)
    header = _format_summary_header(stats, from_id, to_id)

    grouped: dict[str, list[DiffSection]] = {
        "renamed": [],
        "moved": [],
        "modified": [],
        "added": [],
        "deleted": [],
    }

    for s in sections:
        if s.type in grouped:
            grouped[s.type].append(s)
        else:
            grouped["modified"].append(s)

    result: list[DiffSection] = []

    # Summary header as a synthetic section
    result.append(DiffSection(type="header", path="", content=header))

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


# ── Structural pre_commands diff helpers ───────────────────────────


def _diff_pre_commands_line(
    old_content: str,
    new_content: str,
    label: str,
) -> str:
    """Line-based diff for tree/git tag output.

    Shows only added and deleted lines, no context.
    """
    old_lines = set(old_content.strip().split("\n"))
    new_lines = set(new_content.strip().split("\n"))

    added = sorted(new_lines - old_lines)
    deleted = sorted(old_lines - new_lines)

    if not added and not deleted:
        return ""

    parts = [f"### {label}\n"]
    for line in deleted:
        parts.append(f"- {line}\n")
    for line in added:
        parts.append(f"+ {line}\n")
    return "".join(parts)


def _diff_pre_commands_marker(
    old_content: str,
    new_content: str,
    label: str,
    marker: str,
    fmt: str,
) -> str:
    """Section-based diff for git log output (marker-delimited)."""
    from .splitter import _split_to_sections

    old_sections = _split_to_sections(old_content, marker)
    new_sections = _split_to_sections(new_content, marker)

    # Compare sections
    result_parts = []
    min_len = min(len(old_sections), len(new_sections))
    for i in range(min_len):
        old_sec = old_sections[i]
        new_sec = new_sections[i]
        if old_sec != new_sec:
            diff = differ_compute_diff(old_sec, new_sec, f"{label} section {i + 1}", fmt=fmt)
            if diff.strip():
                result_parts.append(diff)

    # Extra sections in new
    if len(new_sections) > len(old_sections):
        for i in range(len(old_sections), len(new_sections)):
            result_parts.append(
                differ_compute_diff("", new_sections[i], f"{label} section {i + 1}", fmt=fmt)
            )

    # Extra sections in old
    if len(old_sections) > len(new_sections):
        for i in range(len(new_sections), len(old_sections)):
            result_parts.append(f"### {label} section {i + 1}\n\n[DELETED]\n")

    return "\n".join(result_parts)


def _diff_pre_commands_structural(
    old_content: str,
    new_content: str,
    label: str,
    cmd: str,
    fmt: str = "markdown",
) -> str:
    """Apply structural diff to pre_commands output based on command type.

    - tree*/git tag* → line-based diff (only added/deleted lines)
    - git log* → marker-based diff (section by section)
    - everything else → text-based diff (unchanged)
    """
    cmd_start = cmd.strip().split()[0] if cmd.strip() else ""

    if cmd_start in ("tree", "git") and "tag" in cmd:
        return _diff_pre_commands_line(old_content, new_content, label)

    if cmd_start == "git" and "log" in cmd:
        return _diff_pre_commands_marker(old_content, new_content, label, "\n=== COMMIT:", fmt)

    # Fallback: text-based diff
    return differ_compute_diff(old_content, new_content, label, fmt=fmt)


# ── End structural pre_commands diff ───────────────────────────────


def compute_diff(
    snapshot_id: str,
    profile: dict | None = None,
    fmt: str = "markdown",
    to_snapshot_id: str | None = None,
    flat: bool = False,
) -> list[DiffSection]:
    """Compute diff between a snapshot and current files or another snapshot.

    Profile is resolved in this order:
    1. Explicit profile argument (if given)
    2. Profile stored in snapshot manifest
    3. Error — cannot compute diff without profile

    Includes both directories (scanned) and explicit files from profile.
    Also diffs pre_commands and command output.

    Args:
        snapshot_id: ID of the snapshot to diff against (--from).
        profile: current profile dict. If None, uses profile from manifest.
        fmt: "markdown" or "xml".
        to_snapshot_id: optional second snapshot for cross-snapshot diff.
            If None, diffs against current files on disk.
        flat: if True, return flat list (backward compatible).
            If False, group by type (default for v1.7.0+).

    Returns:
        List of DiffSection objects.
    """
    manifest = load_snapshot(snapshot_id)

    # Resolve profile
    if profile is None:
        profile = _get_profile_from_manifest(manifest)
        if profile is None:
            raise ValueError(
                f"Snapshot '{snapshot_id}' was created with an older version of arachna "
                f"and does not store the full profile. Use --profile to specify a profile."
            )

    snapshot_files = manifest.get("files", {})
    exclude = _get_exclude_patterns(profile)

    # Build old file set from snapshot A
    old_files = {}
    for path, hash_spec in snapshot_files.items():
        old_files[path] = _get_content_from_manifest(path, hash_spec)

    # Build new file set — from second snapshot or from disk
    if to_snapshot_id is not None:
        to_manifest = load_snapshot(to_snapshot_id)
        to_snapshot_files = to_manifest.get("files", {})
        new_files = {}
        for path, hash_spec in to_snapshot_files.items():
            new_files[path] = _get_content_from_manifest(path, hash_spec)
    else:
        new_files = _build_current_files(profile, exclude)

        for path in list(old_files.keys()):
            if path not in new_files and not _path_matches_profile(path, profile):
                del old_files[path]

    sections = _diff_file_sets(old_files, new_files, fmt)

    # ── Diff pre_commands ──────────────────────────────────────────

    snapshot_pre = manifest.get("pre_commands", {})
    current_pre: dict[str, str] = {}

    if to_snapshot_id is not None:
        to_manifest = load_snapshot(to_snapshot_id)
        snapshot_to_pre = to_manifest.get("pre_commands", {})
        for label, hash_spec in snapshot_to_pre.items():
            current_pre[label] = _get_content_from_manifest(label, hash_spec)
    else:
        for cmd in profile.get("pre_commands", []):
            output = run_command(cmd)
            if output.strip():
                label = f"pre: {cmd if len(cmd) <= 50 else cmd[:47] + '...'}"
                current_pre[label] = output

    # Build map of command labels to original commands for structural diff detection
    cmd_map: dict[str, str] = {}
    for cmd in profile.get("pre_commands", []):
        label = f"pre: {cmd if len(cmd) <= 50 else cmd[:47] + '...'}"
        cmd_map[label] = cmd

    for label, hash_spec in snapshot_pre.items():
        old_content = _get_content_from_manifest(label, hash_spec)
        if label in current_pre:
            cmd = cmd_map.get(label, "")
            if cmd:
                diff_output = _diff_pre_commands_structural(
                    old_content, current_pre[label], label, cmd, fmt
                )
            else:
                diff_output = differ_compute_diff(old_content, current_pre[label], label, fmt=fmt)
            if diff_output:
                sections.append(DiffSection(type="modified", path=label, content=diff_output))
        else:
            sections.append(
                DiffSection(type="deleted", path=label, content=f"### {label}\n\n[DELETED]\n")
            )

    for label in current_pre:
        if label not in snapshot_pre:
            cmd = cmd_map.get(label, "")
            if cmd:
                diff_output = _diff_pre_commands_structural("", current_pre[label], label, cmd, fmt)
            else:
                diff_output = differ_compute_diff("", current_pre[label], label, fmt=fmt)
            sections.append(DiffSection(type="added", path=label, content=diff_output))

    # ── Diff command ───────────────────────────────────────────────

    snapshot_cmd = manifest.get("command", {})
    current_cmd_output = ""

    if to_snapshot_id is not None:
        to_manifest = load_snapshot(to_snapshot_id)
        snapshot_to_cmd = to_manifest.get("command", {})
        for label, hash_spec in snapshot_to_cmd.items():
            current_cmd_output = _get_content_from_manifest(label, hash_spec)
    else:
        cmd = profile.get("command")
        if cmd:
            output = run_command(cmd)
            if output.strip():
                current_cmd_output = output

    if snapshot_cmd and current_cmd_output:
        for label, hash_spec in snapshot_cmd.items():
            old_content = _get_content_from_manifest(label, hash_spec)
            diff_output = differ_compute_diff(old_content, current_cmd_output, label, fmt=fmt)
            if diff_output:
                sections.append(DiffSection(type="modified", path=label, content=diff_output))
    elif snapshot_cmd and not current_cmd_output:
        for label in snapshot_cmd:
            sections.append(
                DiffSection(type="deleted", path=label, content=f"### {label}\n\n[DELETED]\n")
            )
    elif not snapshot_cmd and current_cmd_output:
        diff_output = differ_compute_diff("", current_cmd_output, "command output", fmt=fmt)
        sections.append(DiffSection(type="added", path="command output", content=diff_output))

    # Group by type (default) or return flat
    if not flat and sections:
        sections = _group_diff_sections(sections, snapshot_id, to_snapshot_id)

    return sections


def _path_matches_profile(path: str, profile: dict) -> bool:
    """Check if a relative path matches the current profile's directory/pattern settings.

    Used to distinguish "file deleted from disk" from "file no longer
    in profile config". Checks both directories and explicit files.
    If the path still matches the profile but the
    file is gone -> genuinely deleted. If the path doesn't match the
    profile -> user changed config, ignore.
    """
    if path in profile.get("files", []):
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
