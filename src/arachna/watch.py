"""Public Watch API for arachna v2.0.0."""

import hashlib
import logging
from pathlib import Path

from .api_errors import (
    ProfileNotFoundError,
    SnapshotExistsError,
    SnapshotNotFoundError,
)
from .api_types import (
    DiffResult,
    DiffSection,
    DiffStats,
    GCResult,
    SnapshotInfo,
    StoreStats,
)
from .config import get_profile
from .differ import compute_diff_stats
from .store import (
    create_snapshot as _store_create,
)
from .store import (
    delete_snapshot as _store_delete,
)
from .store import (
    gc as _store_gc,
)
from .store import (
    list_snapshots as _store_list,
)
from .store import (
    load_snapshot as _store_load,
)
from .store import (
    read_object,
)
from .store import (
    stats as _store_stats,
)
from .store import (
    update_snapshot as _store_update,
)
from .store_errors import ObjectNotFoundError as _ObjectNotFoundError
from .store_errors import SnapshotExistsError as _StoreSnapshotExistsError
from .watcher import _collect_snapshot_content
from .watcher import compute_diff as _watcher_compute_diff

logger = logging.getLogger("arachna.watch")


def create_snapshot(profile: str | dict = "full", name: str | None = None) -> str:
    if name is None:
        raise ValueError("name is required for create_snapshot()")
    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    else:
        profile_dict = profile
    files, pre_commands_data, command_data = _collect_snapshot_content(profile_dict)
    try:
        return _store_create(
            files,
            profile_dict=profile_dict,
            name=name,
            pre_commands=pre_commands_data if pre_commands_data else None,
            command=command_data if command_data else None,
        )
    except _StoreSnapshotExistsError as e:
        raise SnapshotExistsError(str(e)) from e


def list_snapshots() -> list[SnapshotInfo]:
    manifests = _store_list()
    result = []
    for m in manifests:
        result.append(
            SnapshotInfo(
                id=m["id"],
                name=m.get("name"),
                created=m.get("created", ""),
                profile=m.get("profile", {}),
                file_count=len(m.get("files", {})),
                pre_commands_count=len(m.get("pre_commands", {})),
                command_count=len(m.get("command", {})),
            )
        )
    return result


def update_snapshot(snapshot_id: str, profile: str | dict | None = None) -> str:
    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    elif isinstance(profile, dict):
        profile_dict = profile
    else:
        profile_dict = None
    try:
        manifest = _store_load(snapshot_id)
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e
    if profile_dict is None:
        stored = manifest.get("profile", {})
        if isinstance(stored, dict):
            profile_dict = stored
        else:
            raise ValueError(
                f"Snapshot '{snapshot_id}' has legacy format. Provide profile explicitly."
            )
    files, pre_commands_data, command_data = _collect_snapshot_content(profile_dict)
    try:
        return _store_update(
            snapshot_id,
            files,
            profile_dict=profile_dict,
            pre_commands=pre_commands_data if pre_commands_data else None,
            command=command_data if command_data else None,
        )
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e


def delete_snapshot(snapshot_id: str) -> None:
    try:
        _store_delete(snapshot_id)
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e


def snapshot_info(snapshot_id: str) -> SnapshotInfo:
    try:
        manifest = _store_load(snapshot_id)
    except _ObjectNotFoundError as e:
        raise SnapshotNotFoundError(str(e)) from e
    return SnapshotInfo(
        id=manifest["id"],
        name=manifest.get("name"),
        created=manifest.get("created", ""),
        profile=manifest.get("profile", {}),
        file_count=len(manifest.get("files", {})),
        pre_commands_count=len(manifest.get("pre_commands", {})),
        command_count=len(manifest.get("command", {})),
    )


def compute_diff(
    snapshot_id: str | None = None,
    profile: str | dict = "full",
    fmt: str = "markdown",
    to_snapshot_id: str | None = None,
    mode: str = "full",
    flat: bool = False,
) -> DiffResult:
    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    else:
        profile_dict = profile
    if snapshot_id is None:
        snaps = _store_list()
        if len(snaps) == 0:
            raise SnapshotNotFoundError("No snapshots found.")
        elif len(snaps) == 1:
            snapshot_id = snaps[0]["id"]
        else:
            raise ValueError(
                f"Multiple snapshots found. Specify snapshot_id from: {', '.join(s['id'] for s in snaps)}"
            )
    sections = _watcher_compute_diff(
        snapshot_id, profile_dict, fmt=fmt, to_snapshot_id=to_snapshot_id, flat=flat
    )
    if mode == "structural" and sections:
        sections = _apply_structural_diff(sections, fmt)
    elif mode == "repo-map" and sections:
        sections = _apply_repo_map_diff(sections, snapshot_id, to_snapshot_id, profile_dict)
    api_sections = [
        DiffSection(
            type=s.type,
            path=s.path,
            old_path=s.old_path,
            similarity=s.similarity,
            content=s.content,
        )
        for s in sections
    ]
    raw_stats = compute_diff_stats(sections)
    stats = DiffStats(
        modified=raw_stats["modified"],
        added=raw_stats["added"],
        deleted=raw_stats["deleted"],
        renamed=raw_stats.get("renamed", 0),
        moved=raw_stats.get("moved", 0),
        tokens=raw_stats["tokens"],
    )
    return DiffResult(
        snapshot_id=snapshot_id, to_snapshot_id=to_snapshot_id, stats=stats, sections=api_sections
    )


def _apply_structural_diff(sections: list, fmt: str) -> list:
    from .differ_structural import structural_diff_sections

    return structural_diff_sections(sections, fmt)


def _apply_repo_map_diff(
    sections: list, snapshot_id: str, to_snapshot_id: str | None, profile: dict
) -> list:
    from .formatter import lang_for_path

    manifest = _store_load(snapshot_id)
    snapshot_files = manifest.get("files", {})
    to_files = None
    if to_snapshot_id:
        to_manifest = _store_load(to_snapshot_id)
        to_files = to_manifest.get("files", {})

    result = []
    for s in sections:
        if s.type in ("header",) or not s.path:
            result.append(s)
            continue
        lang = lang_for_path(Path(s.path))
        if s.type == "modified":
            old_content = _read_file_from_store(s.path, snapshot_files)
            new_content = (
                _read_file_from_disk(s.path)
                if to_files is None
                else _read_file_from_store(s.path, to_files)
            )
            if old_content is not None and new_content is not None:
                old_blocks = _parse_blocks(old_content, lang)
                new_blocks = _parse_blocks(new_content, lang)
                s.content = _format_repo_map_diff(s.path, lang, old_blocks, new_blocks)
            else:
                logger.warning("repo-map: cannot read content for %s, keeping text diff", s.path)
        elif s.type == "added":
            new_content = (
                _read_file_from_disk(s.path)
                if to_files is None
                else _read_file_from_store(s.path, to_files)
            )
            if new_content is not None:
                blocks = _parse_blocks(new_content, lang)
                s.content = _format_repo_map_added(s.path, lang, blocks)
        elif s.type == "deleted":
            old_content = _read_file_from_store(s.path, snapshot_files)
            if old_content is not None:
                blocks = _parse_blocks(old_content, lang)
                sig_lines = [f"  {sig}" for sig, _body in blocks.values()]
                if sig_lines:
                    s.content = (
                        f"### {s.path}\n\n[DELETED]\n\nRemoved signatures:\n"
                        + "\n".join(sig_lines)
                        + "\n"
                    )
        result.append(s)
    return result


def _parse_blocks(text: str, lang: str) -> dict[str, tuple[str, str]]:
    from .differ_structural import _parse_c_like_blocks, _parse_python_blocks, _parse_script_blocks

    if lang == "python":
        return _parse_python_blocks(text)
    elif lang in _C_LIKE_LANGS or lang == "gdscript":
        return _parse_c_like_blocks(text, lang)
    elif lang in _SCRIPT_LANGS:
        return _parse_script_blocks(text)
    return {}


_C_LIKE_LANGS = frozenset(
    {
        "javascript",
        "typescript",
        "rust",
        "go",
        "java",
        "cpp",
        "c",
        "csharp",
        "swift",
        "kotlin",
        "php",
        "zig",
        "gleam",
    }
)
_SCRIPT_LANGS = frozenset({"ruby", "elixir", "lua"})


def _format_repo_map_diff(
    path: str,
    lang: str,
    old_blocks: dict[str, tuple[str, str]],
    new_blocks: dict[str, tuple[str, str]],
) -> str:
    all_names = set(old_blocks.keys()) | set(new_blocks.keys())
    parts = [f"### {path}\n"]
    for name in sorted(all_names):
        old = old_blocks.get(name)
        new = new_blocks.get(name)
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
            body_changed = _hash_body(old_body) != _hash_body(new_body)
            if sig_changed:
                parts.append(f"~ {old_sig}\n  -> {new_sig}\n")
            elif body_changed:
                parts.append(f"  {old_sig}  (body changed)\n")
    return "".join(parts) if len(parts) > 1 else ""


def _format_repo_map_added(path: str, lang: str, blocks: dict[str, tuple[str, str]]) -> str:
    parts = [f"### {path}\n"]
    for _name, (sig, _body) in blocks.items():
        parts.append(f"+ {sig}\n")
    return "".join(parts) if len(parts) > 1 else ""


def _hash_body(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _read_file_from_store(path: str, files: dict) -> str | None:
    for fpath, hash_spec in files.items():
        if fpath == path:
            obj_hash = hash_spec[7:]
            try:
                return read_object(obj_hash).decode("utf-8")
            except Exception:
                return None
    return None


def _read_file_from_disk(path: str) -> str | None:
    fp = Path(path)
    if not fp.is_file():
        return None
    try:
        return fp.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def store_stats() -> StoreStats:
    raw = _store_stats()
    return StoreStats(
        snapshots=raw["snapshots"],
        objects=raw["objects"],
        total_bytes=raw["total_bytes"],
        unique_bytes=raw["unique_bytes"],
        dedup_pct=raw["dedup_pct"],
    )


def store_gc() -> GCResult:
    raw = _store_gc()
    return GCResult(removed_objects=raw["removed"], freed_bytes=raw["freed_bytes"])
