"""Watcher — orchestration layer between CLI, store, and differ.

Walks project files, creates snapshots, and computes diffs
against previously stored snapshots.
"""

import fnmatch
from pathlib import Path

from .differ import DiffSection
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

    # Add explicitly listed files from profile
    profile_files = _read_profile_files(profile)
    files.update(profile_files)

    # Execute pre_commands and store output as named sections
    pre_commands_data = {}
    for cmd in profile.get("pre_commands", []):
        output = run_command(cmd)
        if output.strip():
            label = cmd if len(cmd) <= 50 else cmd[:47] + "..."
            obj_hash = write_object(output.encode("utf-8"))
            pre_commands_data[f"pre: {label}"] = f"sha256:{obj_hash}"

    # Execute command (for command-based profiles) and store output
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

    # Add explicitly listed files from profile
    profile_files = _read_profile_files(profile)
    for rel_path, content in profile_files.items():
        if rel_path not in current_files:
            current_files[rel_path] = content

    return current_files


def _diff_file_sets(
    old_files: dict[str, str],
    new_files: dict[str, str],
    fmt: str,
) -> list[DiffSection]:
    """Compare two file sets and return DiffSections.

    Args:
        old_files: {path: content} from snapshot.
        new_files: {path: content} from current state.
        fmt: "markdown" or "xml".

    Returns:
        List of DiffSection objects (flat, ungrouped).
    """
    sections = []

    for path, old_content in old_files.items():
        if path in new_files:
            diff_output = differ_compute_diff(old_content, new_files[path], path, fmt=fmt)
            if diff_output:
                sections.append(DiffSection(type="modified", path=path, content=diff_output))
        else:
            sections.append(
                DiffSection(type="deleted", path=path, content=f"### {path}\n\n[DELETED]\n")
            )

    for path, content in new_files.items():
        if path not in old_files:
            diff_output = differ_compute_diff("", content, path, fmt=fmt)
            sections.append(DiffSection(type="added", path=path, content=diff_output))

    return sections


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
        # Cross-snapshot mode: load snapshot B from store
        to_manifest = load_snapshot(to_snapshot_id)
        to_snapshot_files = to_manifest.get("files", {})
        new_files = {}
        for path, hash_spec in to_snapshot_files.items():
            new_files[path] = _get_content_from_manifest(path, hash_spec)
    else:
        # Snapshot vs current files on disk
        new_files = _build_current_files(profile, exclude)

        # Filter deleted files: only report if path still matches profile
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

    for label, hash_spec in snapshot_pre.items():
        old_content = _get_content_from_manifest(label, hash_spec)
        if label in current_pre:
            diff_output = differ_compute_diff(old_content, current_pre[label], label, fmt=fmt)
            if diff_output:
                sections.append(DiffSection(type="modified", path=label, content=diff_output))
        else:
            sections.append(
                DiffSection(type="deleted", path=label, content=f"### {label}\n\n[DELETED]\n")
            )

    for label in current_pre:
        if label not in snapshot_pre:
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

    return sections


def _path_matches_profile(path: str, profile: dict) -> bool:
    """Check if a relative path matches the current profile's directory/pattern settings.

    Used to distinguish "file deleted from disk" from "file no longer
    in profile config". Checks both directories and explicit files.
    If the path still matches the profile but the
    file is gone -> genuinely deleted. If the path doesn't match the
    profile -> user changed config, ignore.
    """
    # Check explicit files list
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

        # Path is under this directory — check patterns
        for pat in patterns:
            if fnmatch.fnmatch(path_obj.name, pat):
                return True

    return False
