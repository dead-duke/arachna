"""File collection."""

import contextlib
from pathlib import Path

from ...config.profile_config import ProfileConfig
from ..cache.cache import get_changed_files, update_cache
from ..compressor import compress as _compress
from ..execution.gitignore import load_gitignore_patterns
from ..formatting.formatter import (
    _apply_repo_map_to_section,
    _generate_header,
    format_file_section,
    is_excluded,
    lang_for_path,
)


def _scan_directory_pattern(dir_path, pattern, exclude):
    seen = []
    if ".." in pattern:
        print(f"  Warning: skipping pattern with '..': {pattern}")
        return seen
    for filepath in sorted(dir_path.rglob(pattern)):
        if not filepath.is_file():
            continue
        if filepath.is_symlink():
            print(f"  Warning: skipping symlink: {filepath}")
            continue
        if is_excluded(filepath, exclude):
            continue
        seen.append(filepath)
    return seen


def _scan_one_directory(directory, patterns, exclude, root):
    seen = []
    dir_path = root / directory
    if not dir_path.is_dir():
        return seen
    if dir_path.is_symlink():
        print(f"  Warning: skipping symlink directory: {dir_path}")
        return seen
    for pattern in patterns:
        seen.extend(_scan_directory_pattern(dir_path, pattern, exclude))
    return seen


def _scan_directories(profile: ProfileConfig, exclude: list[str], root: Path) -> list[Path]:
    seen = []
    for directory in profile.directories:
        seen.extend(_scan_one_directory(directory, profile.patterns, exclude, root))
    return seen


def _format_file_list(
    filepaths,
    tokenizer,
    fmt="markdown",
    include_binary=False,
    binary_extensions=None,
    binary_max_mb=1.0,
    verbose=False,
    include_header=False,
    mode="full",
    line_numbers=False,
    root=None,
):
    results = []
    for filepath in filepaths:
        raw_text = None
        if mode == "repo-map":
            with contextlib.suppress(OSError, UnicodeDecodeError):
                raw_text = filepath.read_text(encoding="utf-8")
        section = format_file_section(
            filepath,
            fmt=fmt,
            include_binary=include_binary,
            binary_extensions=binary_extensions,
            binary_max_mb=binary_max_mb,
            verbose=verbose,
            include_header=include_header,
            line_numbers=line_numbers,
            root=root,
        )
        if section:
            if mode == "repo-map":
                lang = lang_for_path(filepath)
                pre_header = ""
                if include_header and raw_text is not None:
                    pre_header = _generate_header(filepath, raw_text, lang)
                section = _apply_repo_map_to_section(
                    filepath,
                    section,
                    raw_text,
                    lang,
                    fmt,
                    include_header,
                    header=pre_header,
                )
            tokens = tokenizer(section)
            results.append((str(filepath), section, tokens))
    return results


def _collect_directory_sections(
    profile: ProfileConfig,
    exclude,
    tokenizer,
    root,
    incremental=False,
    cache=None,
    verbose=False,
    include_header=False,
    mode="full",
):
    fmt = profile.section_format
    include_binary = profile.include_binary
    binary_extensions = profile.binary_extensions
    binary_max_mb = profile.binary_max_mb
    line_numbers = profile.line_numbers
    seen_files = _scan_directories(profile, exclude, root)
    if incremental and cache is not None:
        changed, new, deleted = get_changed_files(seen_files, cache)
        target_files = changed + new
        for del_path in deleted:
            cache.pop(str(del_path), None)
        if deleted:
            print(f"  Deleted: {len(deleted)} file(s)")
    else:
        target_files = seen_files
    sections = _format_file_list(
        target_files,
        tokenizer=tokenizer,
        fmt=fmt,
        include_binary=include_binary,
        binary_extensions=binary_extensions,
        binary_max_mb=binary_max_mb,
        verbose=verbose,
        include_header=include_header,
        mode=mode,
        line_numbers=line_numbers,
        root=root,
    )
    new_cache = update_cache(target_files, cache or {})
    return sections, new_cache


def _collect_file_sections(
    profile: ProfileConfig,
    exclude,
    tokenizer,
    root,
    verbose=False,
    include_header=False,
    mode="full",
):
    fmt = profile.section_format
    include_binary = profile.include_binary
    binary_extensions = profile.binary_extensions
    binary_max_mb = profile.binary_max_mb
    line_numbers = profile.line_numbers
    filepaths = []
    for filepath_str in profile.files:
        filepath = root / filepath_str
        if not filepath.exists():
            if verbose:
                print(f"  Not found: {filepath}")
            continue
        if is_excluded(filepath, exclude):
            continue
        filepaths.append(filepath)
    return _format_file_list(
        filepaths,
        tokenizer=tokenizer,
        fmt=fmt,
        include_binary=include_binary,
        binary_extensions=binary_extensions,
        binary_max_mb=binary_max_mb,
        verbose=verbose,
        include_header=include_header,
        mode=mode,
        line_numbers=line_numbers,
        root=root,
    )


def _get_profile_files(profile: ProfileConfig, exclude, root):
    filepaths = []
    for filepath_str in profile.files:
        filepath = root / filepath_str
        if not filepath.is_file():
            continue
        if is_excluded(filepath, exclude):
            continue
        filepaths.append(filepath)
    return filepaths


def _get_exclude_patterns(profile: ProfileConfig, root):
    exclude = list(profile.exclude_patterns)
    if profile.use_gitignore:
        exclude.extend(load_gitignore_patterns(root))
    return exclude


def _print_compress_stats(raw_tokens, comp_tokens):
    if raw_tokens > 0:
        pct = (raw_tokens - comp_tokens) / raw_tokens * 100
        print(f"  Compressed: ~{raw_tokens} -> ~{comp_tokens} tokens (-{pct:.0f}%)")


def _format_one_file(
    fp,
    fmt,
    include_binary,
    binary_extensions,
    binary_max_mb,
    verbose,
    include_header,
    do_compress,
    line_numbers=False,
    root=None,
):
    section = format_file_section(
        fp,
        fmt=fmt,
        include_binary=include_binary,
        binary_extensions=binary_extensions,
        binary_max_mb=binary_max_mb,
        verbose=verbose,
        include_header=include_header,
        line_numbers=line_numbers,
        root=root,
    )
    if not section:
        return None
    if do_compress:
        section = _compress(section)
    return (str(fp), section, 0)


def _collect_named_sections(
    profile: ProfileConfig,
    exclude,
    tokenizer,
    root,
    incremental=False,
    cache=None,
    verbose=False,
    include_header=False,
    query=None,
    mode="full",
    graph_cache=None,
):
    from .gatherer_commands import _collect_pre_commands
    from .gatherer_query import _filter_by_query

    if graph_cache is None:
        graph_cache = {}
    named_sections = []
    named_sections.extend(_collect_pre_commands(profile.to_dict(), tokenizer, root))
    dir_sections, new_cache = _collect_directory_sections(
        profile,
        exclude,
        tokenizer,
        root,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
        include_header=include_header,
        mode=mode,
    )
    named_sections.extend(dir_sections)
    named_sections.extend(
        _collect_file_sections(
            profile,
            exclude,
            tokenizer,
            root,
            verbose=verbose,
            include_header=include_header,
            mode=mode,
        )
    )
    if query and query.strip():
        named_sections = _filter_by_query(named_sections, query, graph_cache=graph_cache)
    return named_sections, new_cache
