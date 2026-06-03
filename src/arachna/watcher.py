"""Watcher — orchestration layer between CLI, store, and differ.

Walks project files, creates snapshots, and computes diffs
against previously stored snapshots.
"""

import fnmatch
from pathlib import Path

from .differ import DiffSection
from .differ import compute_diff as differ_compute_diff
from .gatherer import _get_exclude_patterns, _scan_directories
from .store import create_snapshot as store_create_snapshot
from .store import load_snapshot, read_object


def create_snapshot(profile: dict, name: str | None = None) -> str:
    """Walk all files in profile and create a snapshot.

    Reuses existing _scan_directories logic from gatherer.
    Reads file contents, stores in content-addressable store,
    creates manifest, returns snapshot ID.

    Args:
        profile: profile dict (same format as .arachna.json profiles).
        name: optional human-readable name.

    Returns:
        Snapshot ID.
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
            rel_path = str(fp.relative_to(Path.cwd()))
        except ValueError:
            rel_path = str(fp)
        files[rel_path] = content

    profile_name = profile.get("name_template", "full")
    return store_create_snapshot(files, profile=profile_name, name=name)


def compute_diff(
    snapshot_id: str,
    profile: dict,
    fmt: str = "markdown",
) -> list[DiffSection]:
    """Compute diff between a snapshot and current files.

    Args:
        snapshot_id: ID of the snapshot to diff against.
        profile: current profile dict.
        fmt: "markdown" or "xml".

    Returns:
        List of DiffSection objects.
    """
    manifest = load_snapshot(snapshot_id)
    snapshot_files = manifest.get("files", {})

    exclude = _get_exclude_patterns(profile)
    current_filepaths = _scan_directories(profile, exclude)

    # Build set of current file paths (relative)
    current_files = {}
    for fp in current_filepaths:
        try:
            rel_path = str(fp.relative_to(Path.cwd()))
        except ValueError:
            rel_path = str(fp)
        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        current_files[rel_path] = content

    sections = []

    # Check files in snapshot
    for path, hash_spec in snapshot_files.items():
        obj_hash = hash_spec[7:]  # strip "sha256:"

        if path in current_files:
            # File exists in both — check for changes
            old_content = read_object(obj_hash).decode("utf-8")
            new_content = current_files[path]
            diff_output = differ_compute_diff(old_content, new_content, path, fmt=fmt)
            if diff_output:
                sections.append(DiffSection(type="modified", path=path, content=diff_output))
        elif _path_matches_profile(path, profile):
            # File was in snapshot, not on disk, but still matches
            # current profile patterns → genuinely deleted
            sections.append(
                DiffSection(type="deleted", path=path, content=f"### {path}\n\n[DELETED]\n")
            )
        # else: file not on disk AND doesn't match profile patterns
        # → profile changed, ignore

    # Check for new files not in snapshot
    for path, content in current_files.items():
        if path not in snapshot_files:
            diff_output = differ_compute_diff("", content, path, fmt=fmt)
            sections.append(DiffSection(type="added", path=path, content=diff_output))

    return sections


def _path_matches_profile(path: str, profile: dict) -> bool:
    """Check if a relative path matches the current profile's directory/pattern settings.

    Used to distinguish "file deleted from disk" from "file no longer
    in profile config". If the path still matches the profile but the
    file is gone → genuinely deleted. If the path doesn't match the
    profile → user changed config, ignore.
    """
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
