"""Snapshot file collection and diff — file I/O, diff sections, path matching."""

import fnmatch
import logging
from pathlib import Path

from ...config.profile_config import ProfileConfig
from ...domain.api_types import DiffSection
from ...domain.collection.gatherer_files import _get_exclude_patterns, _scan_directories
from ...domain.path_utils import SafePath
from ..rename.snapshot_rename import _detect_renames_and_moves
from ..store.store import _SHA256_PREFIX, load_snapshot, read_object
from ..store.store_errors import CorruptedStoreError, ObjectNotFoundError
from .differ import compute_diff as differ_compute_diff
from .snapshot_diff_helpers import _rel_path

logger = logging.getLogger("arachna.snapshot")


def _read_profile_files(profile: ProfileConfig, root: Path) -> dict[str, str]:
    result = {}
    for filepath_str in profile.files:
        fp = SafePath(filepath_str, root)
        if not fp.is_file():
            continue
        try:
            content = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        result[_rel_path(fp.to_path().resolve(), root)] = content
    return result


def _collect_snapshot_files(profile: ProfileConfig, root: Path) -> dict[str, str]:
    exclude = _get_exclude_patterns(profile, root=root)
    filepaths = _scan_directories(profile, exclude, root=root)
    files = {}
    for fp in filepaths:
        sfp = SafePath(fp, root)
        try:
            content = sfp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        files[_rel_path(fp.resolve(), root)] = content
    profile_files = _read_profile_files(profile, root)
    files.update(profile_files)
    return files


def _get_content_from_manifest(hash_spec: str, root: Path) -> str:
    return read_object(hash_spec[len(_SHA256_PREFIX) :], root=root).decode("utf-8")


def _build_current_files(profile: ProfileConfig, exclude: list[str], root: Path) -> dict[str, str]:
    current_filepaths = _scan_directories(profile, exclude, root=root)
    current_files = {}
    for fp in current_filepaths:
        sfp = SafePath(fp, root)
        try:
            content = sfp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        current_files[_rel_path(fp.resolve(), root)] = content
    profile_files = _read_profile_files(profile, root)
    for rel_path, content in profile_files.items():
        if rel_path not in current_files:
            current_files[rel_path] = content
    return current_files


def _build_deleted_added_dicts(old_files, new_files):
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


def _build_snapshot_files_dict(snapshot_id, root):
    manifest = load_snapshot(snapshot_id, root=root)
    snapshot_files = manifest.get("files", {})
    return {path: _get_content_from_manifest(h, root=root) for path, h in snapshot_files.items()}


def _build_target_files_dict(profile, exclude, root, to_snapshot_id):
    if to_snapshot_id is not None:
        to_manifest = load_snapshot(to_snapshot_id, root=root)
        to_snapshot_files = to_manifest.get("files", {})
        return {
            path: _get_content_from_manifest(h, root=root) for path, h in to_snapshot_files.items()
        }
    return _build_current_files(profile, exclude, root)


def _diff_files_sections(
    snapshot_id, profile, exclude, to_snapshot_id, fmt, root, line_numbers=False
):
    old_files = _build_snapshot_files_dict(snapshot_id, root)
    if to_snapshot_id is None:
        new_files = _build_target_files_dict(profile, exclude, root, to_snapshot_id)
        for path in set(old_files):
            if path not in new_files and not _path_matches_profile(path, profile, root):
                del old_files[path]
    else:
        new_files = _build_target_files_dict(profile, exclude, root, to_snapshot_id)
    return _diff_file_sets(old_files, new_files, fmt, line_numbers=line_numbers)


def _path_matches_profile(path, profile, root):
    normalized_files = [_rel_path(Path(f), root) for f in profile.files]
    if path in normalized_files:
        return True
    directories = profile.directories
    patterns = profile.patterns
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


def _read_file_from_store(path, files, root):
    for fpath, hash_spec in files.items():
        if fpath == path:
            try:
                return read_object(hash_spec[len(_SHA256_PREFIX) :], root=root).decode("utf-8")
            except (OSError, UnicodeDecodeError, ObjectNotFoundError, CorruptedStoreError):
                return None
    return None


def _read_file_from_disk(path, root=None):
    fp = Path(str(path))
    if root is not None:
        sfp = SafePath(fp, root)
        if not sfp.is_file():
            return None
        try:
            return sfp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
    if not fp.is_file():
        return None
    try:
        return fp.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
