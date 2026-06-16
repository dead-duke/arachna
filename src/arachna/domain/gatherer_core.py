# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Core gatherer — file collection and pre_commands for arachna v4.0.1.

Extracted from gatherer.py during v4.0.1 decomposition.
Handles directory scanning, file formatting, and command execution.
"""

import contextlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .cache import get_changed_files, update_cache
from .compressor import compress as _compress
from .formatter import (
    _apply_repo_map_to_section,
    _generate_header,
    format_file_section,
    is_excluded,
    lang_for_path,
)
from .gitignore import load_gitignore_patterns
from .runner import run_command, run_pre_commands
from .tokenizer import count_tokens


def _collect_pre_commands(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int],
    root: Path,
) -> list[tuple[str, str, int]]:
    """Run pre_commands from profile and return labeled output sections.

    Args:
        profile: Profile dict with optional 'pre_commands' list.
        tokenizer: Token counting function.
        root: Project root directory.

    Returns:
        List of (label, output, token_count) tuples.
    """
    results = []
    commands = profile.get("pre_commands", [])
    if not commands:
        return results
    for cmd, output in run_pre_commands(commands, root=root):
        if output.strip():
            tokens = tokenizer(output)
            label = cmd if len(cmd) <= 50 else cmd[:47] + "..."
            results.append((f"pre: {label}", output, tokens))
    return results


def _scan_directories(
    profile: dict[str, Any],
    exclude: list[str],
    root: Path,
) -> list[Path]:
    """Scan profile directories for matching files.

    Handles symlink directories and files (skipped with warning).
    Handles '..' in patterns (skipped with warning).

    Args:
        profile: Profile dict with 'directories' and 'patterns'.
        exclude: List of fnmatch exclude patterns.
        root: Project root directory.

    Returns:
        Sorted list of matching file paths.
    """
    seen = []
    for directory in profile.get("directories", []):
        dir_path = root / directory
        if not dir_path.is_dir():
            continue
        if dir_path.is_symlink():
            print(f"  Warning: skipping symlink directory: {dir_path}")
            continue
        for pattern in profile.get("patterns", ["*"]):
            if ".." in pattern:
                print(f"  Warning: skipping pattern with '..': {pattern}")
                continue
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


def _format_file_list(
    filepaths: list[Path],
    tokenizer: Callable[[str], int],
    fmt: str = "markdown",
    include_binary: bool = False,
    binary_extensions: list[str] | None = None,
    binary_max_mb: float = 1.0,
    verbose: bool = False,
    include_header: bool = False,
    mode: str = "full",
) -> list[tuple[str, str, int]]:
    """Format a list of files into named sections with token counts.

    Args:
        filepaths: List of file paths to format.
        tokenizer: Token counting function.
        fmt: Output format ('markdown', 'xml', 'json').
        include_binary: Whether to include binary files.
        binary_extensions: Allowed binary extensions.
        binary_max_mb: Maximum binary file size in MB.
        verbose: Whether to print skip reasons.
        include_header: Whether to include deps/exports header.
        mode: Collection mode ('full', 'repo-map', 'headers').

    Returns:
        List of (filepath, formatted_section, token_count) tuples.
    """
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
    profile: dict[str, Any],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    root: Path,
    incremental: bool = False,
    cache: dict[str, float] | None = None,
    verbose: bool = False,
    include_header: bool = False,
    mode: str = "full",
) -> tuple[list[tuple[str, str, int]], dict[str, float] | None]:
    """Collect formatted sections from profile directories.

    Supports incremental mode via file modification cache.

    Args:
        profile: Profile dict.
        exclude: List of fnmatch exclude patterns.
        tokenizer: Token counting function.
        root: Project root directory.
        incremental: Whether to use incremental mode.
        cache: File modification cache for incremental mode.
        verbose: Whether to print progress.
        include_header: Whether to include deps/exports header.
        mode: Collection mode.

    Returns:
        Tuple of (sections_list, updated_cache_or_None).
    """
    fmt = profile.get("section_format", "markdown")
    include_binary = profile.get("include_binary", False)
    binary_extensions = profile.get("binary_extensions")
    binary_max_mb = profile.get("binary_max_mb", 1.0)
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
    )
    new_cache = update_cache(target_files, cache or {})
    return sections, new_cache


def _collect_file_sections(
    profile: dict[str, Any],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    root: Path,
    verbose: bool = False,
    include_header: bool = False,
    mode: str = "full",
) -> list[tuple[str, str, int]]:
    """Collect formatted sections from explicitly listed files.

    Args:
        profile: Profile dict with optional 'files' list.
        exclude: List of fnmatch exclude patterns.
        tokenizer: Token counting function.
        root: Project root directory.
        verbose: Whether to print skip reasons.
        include_header: Whether to include deps/exports header.
        mode: Collection mode.

    Returns:
        List of (filepath, formatted_section, token_count) tuples.
    """
    fmt = profile.get("section_format", "markdown")
    include_binary = profile.get("include_binary", False)
    binary_extensions = profile.get("binary_extensions")
    binary_max_mb = profile.get("binary_max_mb", 1.0)
    file_paths_str = profile.get("files", [])
    filepaths = []
    for filepath_str in file_paths_str:
        filepath = Path(filepath_str)
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
    )


def _get_profile_files(profile: dict[str, Any], exclude: list[str]) -> list[Path]:
    """Get list of existing, non-excluded files from profile.files.

    Args:
        profile: Profile dict with optional 'files' list.
        exclude: List of fnmatch exclude patterns.

    Returns:
        List of valid file paths.
    """
    filepaths = []
    for filepath_str in profile.get("files", []):
        filepath = Path(filepath_str)
        if not filepath.is_file():
            continue
        if is_excluded(filepath, exclude):
            continue
        filepaths.append(filepath)
    return filepaths


def _get_exclude_patterns(profile: dict[str, Any], root: Path) -> list[str]:
    """Combine profile exclude_patterns with gitignore patterns.

    Args:
        profile: Profile dict.
        root: Project root directory.

    Returns:
        Combined list of fnmatch exclude patterns.
    """
    exclude = list(profile.get("exclude_patterns", []))
    if profile.get("use_gitignore", True):
        exclude.extend(load_gitignore_patterns(root))
    return exclude


def _print_compress_stats(raw_tokens: int, comp_tokens: int) -> None:
    """Print compression statistics to stdout.

    Args:
        raw_tokens: Token count before compression.
        comp_tokens: Token count after compression.
    """
    if raw_tokens > 0:
        pct = (raw_tokens - comp_tokens) / raw_tokens * 100
        print(f"  Compressed: ~{raw_tokens} -> ~{comp_tokens} tokens (-{pct:.0f}%)")


def _format_one_file(
    fp: Path,
    fmt: str,
    include_binary: bool,
    binary_extensions: list[str] | None,
    binary_max_mb: float,
    verbose: bool,
    include_header: bool,
    do_compress: bool,
) -> tuple[str, str, int] | None:
    """Format a single file and optionally compress. Used by parallel I/O.

    Args:
        fp: File path.
        fmt: Output format.
        include_binary: Whether to include binary files.
        binary_extensions: Allowed binary extensions.
        binary_max_mb: Maximum binary file size in MB.
        verbose: Whether to print skip reasons.
        include_header: Whether to include deps/exports header.
        do_compress: Whether to apply whitespace compression.

    Returns:
        Tuple of (filepath_str, formatted_content, 0) or None if skipped.
    """
    section = format_file_section(
        fp,
        fmt=fmt,
        include_binary=include_binary,
        binary_extensions=binary_extensions,
        binary_max_mb=binary_max_mb,
        verbose=verbose,
        include_header=include_header,
    )
    if not section:
        return None
    if do_compress:
        section = _compress(section)
    return (str(fp), section, 0)


def gather_files(
    profile: dict[str, Any],
    root: Path,
    verbose: bool = False,
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """Gather files by profile, return list of formatted content strings.

    Args:
        profile: Profile dict.
        root: Project root directory.
        verbose: Whether to print progress.
        tokenizer: Token counting function (default: count_tokens).

    Returns:
        List of formatted file content strings.
    """
    tk = tokenizer if tokenizer is not None else count_tokens
    exclude = _get_exclude_patterns(profile, root=root)
    sections, _ = _collect_named_sections(
        profile, exclude, tokenizer=tk, root=root, verbose=verbose
    )
    return [content for _, content, _ in sections]


def gather_command(cmd: str, root: Path) -> str:
    """Execute a shell command and return its output.

    Args:
        cmd: Shell command to execute.
        root: Project root directory.

    Returns:
        Command stdout as string.
    """
    return run_command(cmd, root=root, allow_file_args=True)


def _collect_named_sections(
    profile,
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
    """Collect all named sections: pre_commands + directories + explicit files.

    Args:
        profile: Profile dict.
        exclude: List of fnmatch exclude patterns.
        tokenizer: Token counting function.
        root: Project root directory.
        incremental: Whether to use incremental mode.
        cache: File modification cache.
        verbose: Whether to print progress.
        include_header: Whether to include deps/exports header.
        query: Optional query string for filtering.
        mode: Collection mode.
        graph_cache: Import graph cache for query filtering.

    Returns:
        Tuple of (named_sections_list, updated_cache).
    """
    from .gatherer_query import _filter_by_query

    if graph_cache is None:
        graph_cache = {}
    named_sections = []
    named_sections.extend(_collect_pre_commands(profile, tokenizer, root))
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
