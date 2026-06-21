"""Repo-map diff transformation — signatures only for modified/added/deleted sections."""

import hashlib
from pathlib import Path

from ..domain.formatting.formatter import C_LIKE_LANGS, lang_for_path
from ..domain.tokenization.language_dispatch import get_block_parser
from .snapshot_diff_files import _read_file_from_disk, _read_file_from_store
from .store import load_snapshot


def _get_snapshot_files(snapshot_id, to_snapshot_id, root):
    manifest = load_snapshot(snapshot_id, root=root)
    snapshot_files = manifest.get("files", {})
    to_files = None
    if to_snapshot_id:
        to_manifest = load_snapshot(to_snapshot_id, root=root)
        to_files = to_manifest.get("files", {})
    return snapshot_files, to_files


def _parse_blocks_for_lang(content, lang, parser):
    if content is None or parser is None:
        return None
    if lang in C_LIKE_LANGS or lang == "gdscript":
        return parser(content, lang)
    return parser(content)


def _repo_map_modified_section(s, lang, parser, snapshot_files, to_files, root):
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
    new_content = (
        _read_file_from_disk(root / s.path, root)
        if to_files is None
        else _read_file_from_store(s.path, to_files, root)
    )
    blocks = _parse_blocks_for_lang(new_content, lang, parser)
    if blocks is not None:
        s.content = _format_repo_map_added(s.path, blocks)


def _repo_map_deleted_section(s, lang, parser, snapshot_files, root):
    old_content = _read_file_from_store(s.path, snapshot_files, root)
    blocks = _parse_blocks_for_lang(old_content, lang, parser)
    if blocks is not None:
        sig_lines = [f"  {sig}" for sig, _body in blocks.values()]
        if sig_lines:
            s.content = (
                f"### {s.path}\n\n[DELETED]\n\nRemoved signatures:\n" + "\n".join(sig_lines) + "\n"
            )


def _format_repo_map_entry(old, new, parts):
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
    all_names = set(old_blocks.keys()) | set(new_blocks.keys())
    parts = [f"### {path}\n"]
    for name in sorted(all_names):
        old = old_blocks.get(name)
        new = new_blocks.get(name)
        _format_repo_map_entry(old, new, parts)
    return "".join(parts) if len(parts) > 1 else ""


def _format_repo_map_added(path, blocks):
    parts = [f"### {path}\n"]
    for _name, (sig, _body) in blocks.items():
        parts.append(f"+ {sig}\n")
    return "".join(parts) if len(parts) > 1 else ""


def apply_repo_map_to_sections(sections, snapshot_id, to_snapshot_id, root):
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
