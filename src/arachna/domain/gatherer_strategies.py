# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Collection strategies for arachna v4.0.1.

Extracted from gatherer.py during v4.0.1 decomposition.
Strategy pattern for full/repo-map/headers collection modes.
Each strategy encapsulates its own import graph cache.
"""

import os as _os
import sys
from typing import Any

from .compressor import compress as _compress
from .gatherer_core import (
    _collect_pre_commands,
    _format_one_file,
    _get_profile_files,
    _print_compress_stats,
    _scan_directories,
)
from .gatherer_query import _filter_by_query, _filter_filenames_by_query
from .splitter import pack_into_parts, split_sections


class _FullModeStrategy:
    """Strategy for full content collection mode.

    Collects complete file contents, supports parallel I/O via
    ThreadPoolExecutor when ARACHNA_MAX_WORKERS > 1.
    Encapsulates import graph cache for query filtering.
    """

    def __init__(self):
        self._graph_cache: dict = {}

    def assemble(self, profile, exclude, tokenizer, root, incremental, cache, verbose, query):
        from .cache import get_changed_files, update_cache

        do_compress = profile.get("compress", False)
        max_tokens = profile.get("max_tokens", 16000)
        include_header = bool(query and query.strip())
        filepaths = _scan_directories(profile, exclude, root)
        profile_files = _get_profile_files(profile, exclude)
        for fp in profile_files:
            if fp not in filepaths:
                filepaths.append(fp)
        if incremental and cache is not None:
            changed, new, deleted = get_changed_files(filepaths, cache)
            target_files = changed + new
            for del_path in deleted:
                cache.pop(str(del_path), None)
            if deleted:
                print(f"  Deleted: {len(deleted)} file(s)")
        else:
            target_files = filepaths
        if query and query.strip():
            target_files = _filter_filenames_by_query(target_files, query)
        pre_sections = _collect_pre_commands(profile, tokenizer, root)
        new_cache = update_cache(target_files, cache or {})
        fmt = profile.get("section_format", "markdown")
        include_binary = profile.get("include_binary", False)
        binary_extensions = profile.get("binary_extensions")
        binary_max_mb = profile.get("binary_max_mb", 1.0)
        sections = []
        named_sections = list(pre_sections)
        for _i, (_label, output, _tokens) in enumerate(pre_sections):
            content = _compress(output) if do_compress and output.strip() else output
            sections.append(content)
        total_files = len(target_files)
        if verbose and total_files > 100:
            print(f"  Collecting... 0/{total_files} files", file=sys.stderr)
        max_workers = int(_os.environ.get("ARACHNA_MAX_WORKERS", "1"))
        if max_workers > 1 and total_files > 1:
            self._collect_parallel(
                target_files,
                fmt,
                include_binary,
                binary_extensions,
                binary_max_mb,
                verbose,
                include_header,
                do_compress,
                max_workers,
                total_files,
                sections,
                named_sections,
                tokenizer,
            )
        else:
            self._collect_sequential(
                target_files,
                fmt,
                include_binary,
                binary_extensions,
                binary_max_mb,
                verbose,
                include_header,
                do_compress,
                total_files,
                sections,
                named_sections,
                tokenizer,
            )
        if query and query.strip():
            named_sections = _filter_by_query(named_sections, query, graph_cache=self._graph_cache)
        if max_tokens == 0:
            all_content = "\n\n".join(s.strip() for s in sections if s.strip())
            all_indices = [list(range(len(named_sections)))]
            parts = [all_content]
            indices = all_indices
        else:
            parts, indices = pack_into_parts(sections, max_tokens, tokenizer=tokenizer)
        if verbose and do_compress:
            raw_tokens = sum(tokens for _name, _content, tokens in named_sections)
            comp_tokens = sum(tokenizer(p) for p in parts)
            _print_compress_stats(raw_tokens, comp_tokens)
        return named_sections, parts, indices, new_cache

    def _collect_parallel(
        self,
        target_files,
        fmt,
        include_binary,
        binary_extensions,
        binary_max_mb,
        verbose,
        include_header,
        do_compress,
        max_workers,
        total_files,
        sections,
        named_sections,
        tokenizer,
    ):
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        _format_one_file,
                        fp,
                        fmt,
                        include_binary,
                        binary_extensions,
                        binary_max_mb,
                        verbose,
                        include_header,
                        do_compress,
                    ): idx
                    for idx, fp in enumerate(target_files)
                }
                results_map: dict[int, tuple[str, str, int]] = {}
                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        results_map[futures[future]] = result
                    if verbose and total_files > 100 and len(results_map) % 100 == 0:
                        print(
                            f"  collected {len(results_map)}/{total_files} files...",
                            file=sys.stderr,
                        )
            for idx in range(len(target_files)):
                if idx in results_map:
                    fp_str, content, _ = results_map[idx]
                    tokens = tokenizer(content)
                    sections.append(content)
                    named_sections.append((fp_str, content, tokens))
        except ImportError:
            self._collect_sequential(
                target_files,
                fmt,
                include_binary,
                binary_extensions,
                binary_max_mb,
                verbose,
                include_header,
                do_compress,
                total_files,
                sections,
                named_sections,
                tokenizer,
            )

    def _collect_sequential(
        self,
        target_files,
        fmt,
        include_binary,
        binary_extensions,
        binary_max_mb,
        verbose,
        include_header,
        do_compress,
        total_files,
        sections,
        named_sections,
        tokenizer,
    ):
        for idx, fp in enumerate(target_files):
            result = _format_one_file(
                fp,
                fmt,
                include_binary,
                binary_extensions,
                binary_max_mb,
                verbose,
                include_header,
                do_compress,
            )
            if result is not None:
                fp_str, content, _ = result
                tokens = tokenizer(content)
                sections.append(content)
                named_sections.append((fp_str, content, tokens))
            if verbose and total_files > 100 and (idx + 1) % 100 == 0:
                print(
                    f"  collected {idx + 1}/{total_files} files...",
                    file=sys.stderr,
                )


class _RepoMapModeStrategy:
    """Strategy for repo-map collection mode (signatures only)."""

    def __init__(self):
        self._graph_cache: dict = {}

    def assemble(self, profile, exclude, tokenizer, root, incremental, cache, verbose, query):
        return _assemble_in_memory(
            profile,
            exclude,
            tokenizer,
            root,
            incremental,
            cache,
            verbose,
            query,
            "repo-map",
            graph_cache=self._graph_cache,
        )


class _HeadersModeStrategy:
    """Strategy for headers-only collection mode (deps/exports only)."""

    def __init__(self):
        self._graph_cache: dict = {}

    def assemble(self, profile, exclude, tokenizer, root, incremental, cache, verbose, query):
        return _assemble_in_memory(
            profile,
            exclude,
            tokenizer,
            root,
            incremental,
            cache,
            verbose,
            query,
            "headers",
            graph_cache=self._graph_cache,
        )


_MODE_STRATEGIES: dict[str, Any] | None = None


def _get_mode_strategies() -> dict[str, Any]:
    """Lazy-init and return mode strategy mapping.

    Returns:
        Dict mapping mode name to strategy instance.
    """
    global _MODE_STRATEGIES
    if _MODE_STRATEGIES is None:
        _MODE_STRATEGIES = {
            "full": _FullModeStrategy(),
            "repo-map": _RepoMapModeStrategy(),
            "headers": _HeadersModeStrategy(),
        }
    return _MODE_STRATEGIES


def _assemble_in_memory(
    profile, exclude, tokenizer, root, incremental, cache, verbose, query, mode, graph_cache=None
):
    """Assemble content in memory for repo-map and headers modes.

    Uses two-pass approach: metadata pass then packing pass.
    """
    from .gatherer_core import _collect_named_sections

    if graph_cache is None:
        graph_cache = {}
    do_compress = profile.get("compress", False)
    max_tokens = profile.get("max_tokens", 16000)
    include_header = bool(query and query.strip()) or mode == "headers"
    named_sections, new_cache = _collect_named_sections(
        profile,
        exclude,
        tokenizer,
        root,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
        include_header=include_header,
        query=query,
        mode=mode,
        graph_cache=graph_cache,
    )
    sections = []
    raw_tokens = 0
    for _name, content, tokens in named_sections:
        raw_tokens += tokens
        if do_compress and content.strip():
            sections.append(_compress(content))
        else:
            sections.append(content)
    if max_tokens == 0:
        all_content = "\n\n".join(s.strip() for s in sections if s.strip())
        all_indices = [list(range(len(named_sections)))]
        parts = [all_content]
        indices = all_indices
    else:
        if verbose and do_compress:
            comp_tokens = sum(tokenizer(s) for s in sections)
            _print_compress_stats(raw_tokens, comp_tokens)
        parts, indices = split_sections(sections, max_tokens, separator="\n\n", tokenizer=tokenizer)
    return named_sections, parts, indices, new_cache
