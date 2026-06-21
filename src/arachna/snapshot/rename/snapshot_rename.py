"""Rename/move detection between snapshots — exact hash and similarity matching."""

import difflib
from pathlib import Path

from ...domain.api_types import DiffSection
from ..diff.differ import compute_diff as differ_compute_diff

_MAX_SIMILARITY_SIZE = 1_048_576


def _build_hash_index(items):
    from ..diff.snapshot_diff import _content_hash

    index = {}
    for path, content in items.items():
        index.setdefault(_content_hash(content), []).append(path)
    return index


def _add_exact_rename_section(sections, old_path, new_path):
    old_dir = str(Path(old_path).parent)
    new_dir = str(Path(new_path).parent)
    old_name = Path(old_path).name
    new_name = Path(new_path).name
    if old_dir == new_dir and old_name != new_name:
        sections.append(
            DiffSection(
                type="renamed",
                path=new_path,
                old_path=old_path,
                similarity=1.0,
                content=f"RENAMED: {old_path} -> {new_path}\n",
            )
        )
    elif old_dir != new_dir and old_name == new_name:
        sections.append(
            DiffSection(
                type="moved",
                path=new_path,
                old_path=old_path,
                similarity=1.0,
                content=f"MOVED: {old_path} -> {new_path}\n",
            )
        )
    else:
        sections.append(
            DiffSection(
                type="renamed",
                path=new_path,
                old_path=old_path,
                similarity=1.0,
                content=f"MOVED AND RENAMED: {old_path} -> {new_path}\n",
            )
        )


def _process_hash_group(del_paths, add_paths, rename_sections, matched_deleted, matched_added):
    if len(del_paths) == 1 and len(add_paths) == 1:
        old_path = del_paths[0]
        new_path = add_paths[0]
        if old_path == new_path:
            matched_deleted.add(old_path)
            matched_added.add(new_path)
        else:
            _add_exact_rename_section(rename_sections, old_path, new_path)
            matched_deleted.add(old_path)
            matched_added.add(new_path)
    else:
        matched_deleted.update(del_paths)
        matched_added.update(add_paths)


def _match_exact_renames(deleted, added):
    rename_sections = []
    matched_deleted = set()
    matched_added = set()
    deleted_by_hash = _build_hash_index(deleted)
    added_by_hash = _build_hash_index(added)
    for ch, del_paths in deleted_by_hash.items():
        if ch not in added_by_hash:
            continue
        add_paths = added_by_hash[ch]
        _process_hash_group(del_paths, add_paths, rename_sections, matched_deleted, matched_added)
    remaining_deleted = {p: c for p, c in deleted.items() if p not in matched_deleted}
    remaining_added = {p: c for p, c in added.items() if p not in matched_added}
    return rename_sections, matched_deleted, matched_added, remaining_deleted, remaining_added


def _is_candidate_for_similarity(
    del_path, del_content, remaining_added, matched_added, newly_matched_added
):
    from ..diff.snapshot_diff import _is_binary_content

    if _is_binary_content(del_content) or len(del_content.encode("utf-8")) > _MAX_SIMILARITY_SIZE:
        return {}
    del_ext = Path(del_path).suffix
    return {
        p: c
        for p, c in remaining_added.items()
        if Path(p).suffix == del_ext
        and p not in matched_added
        and p not in newly_matched_added
        and len(c.encode("utf-8")) <= _MAX_SIMILARITY_SIZE
    }


def _try_similar_match(
    del_path, del_content, candidates, newly_matched_added, remaining_added, fmt, line_numbers
):
    from ..diff.snapshot_diff import _is_binary_content

    for add_path, add_content in candidates.items():
        if _is_binary_content(add_content):
            continue
        ratio = difflib.SequenceMatcher(None, del_content, add_content).ratio()
        if ratio > 0.7:
            section = _build_similar_rename_section(
                del_path, add_path, del_content, add_content, ratio, fmt, line_numbers
            )
            newly_matched_added.add(add_path)
            del remaining_added[add_path]
            return section
    return None


def _build_similar_rename_section(
    del_path, add_path, del_content, add_content, ratio, fmt, line_numbers
):
    old_dir = str(Path(del_path).parent)
    new_dir = str(Path(add_path).parent)
    old_name = Path(del_path).name
    new_name = Path(add_path).name
    if old_dir == new_dir:
        action = f"RENAMED: {del_path} -> {add_path} ({ratio:.0%} similar)"
        section_type = "renamed"
    elif old_name == new_name:
        action = f"MOVED: {del_path} -> {add_path} ({ratio:.0%} similar)"
        section_type = "moved"
    else:
        action = f"MOVED AND RENAMED: {del_path} -> {add_path} ({ratio:.0%} similar)"
        section_type = "renamed"
    diff_output = differ_compute_diff(
        del_content, add_content, add_path, fmt=fmt, line_numbers=line_numbers
    )
    content = f"{action}\n\n{diff_output}" if diff_output else f"{action}\n"
    return DiffSection(
        type=section_type, path=add_path, old_path=del_path, similarity=ratio, content=content
    )


def _match_similar_renames(
    remaining_deleted, remaining_added, matched_added, fmt, line_numbers=False
):
    rename_sections = []
    matched_deleted = set()
    newly_matched_added = set()
    for del_path, del_content in remaining_deleted.items():
        candidates = _is_candidate_for_similarity(
            del_path, del_content, remaining_added, matched_added, newly_matched_added
        )
        if not candidates:
            continue
        section = _try_similar_match(
            del_path,
            del_content,
            candidates,
            newly_matched_added,
            remaining_added,
            fmt,
            line_numbers,
        )
        if section is not None:
            rename_sections.append(section)
            matched_deleted.add(del_path)
    return rename_sections, matched_deleted, newly_matched_added


def _detect_renames_and_moves(deleted, added, fmt, line_numbers=False):
    exact_sections, exact_del, exact_add, remaining_del, remaining_add = _match_exact_renames(
        deleted, added
    )
    similar_sections, similar_del, similar_add = _match_similar_renames(
        remaining_del, remaining_add, exact_add, fmt, line_numbers=line_numbers
    )
    return (exact_sections + similar_sections, exact_del | similar_del, exact_add | similar_add)
