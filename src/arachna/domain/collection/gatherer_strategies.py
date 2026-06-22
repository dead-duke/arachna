"""Collection strategies."""

import functools
import os as _os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...config import CollectionMode
from ..compressor import compress as _compress
from ..execution.splitter import pack_into_parts, split_sections
from .gatherer_files import (
    _format_one_file,
    _get_profile_files,
    _print_compress_stats,
    _scan_directories,
)
from .gatherer_query import _filter_by_query, _filter_filenames_by_query


@dataclass
class _CollectParams:
    target_files: list[Path]
    fmt: str
    include_binary: bool
    binary_extensions: list[str] | None
    binary_max_mb: float
    verbose: bool
    include_header: bool
    do_compress: bool
    max_workers: int
    total_files: int
    sections: list[str]
    named_sections: list[tuple[str, str, int]]
    tokenizer: Any
    line_numbers: bool = False
    root: Path | None = None


class _FullModeStrategy:
    """Strategy for 'full' collection mode — all file content."""

    def __init__(self):
        self._graph_cache: dict = {}

    def _resolve_target_files(self, profile, exclude, root, incremental, cache, query):
        from ..cache.cache import get_changed_files, update_cache

        filepaths = _scan_directories(profile, exclude, root)
        for fp in _get_profile_files(profile, exclude, root):
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
        return target_files, update_cache(target_files, cache or {})

    def _build_collect_params(self, target_files, profile, pre_sections, tokenizer, root, query):
        do_compress = profile.compress
        fmt = profile.section_format
        sections = []
        named_sections = list(pre_sections)
        for _i, (_label, output, _tokens) in enumerate(pre_sections):
            sections.append(_compress(output) if do_compress and output.strip() else output)
        return _CollectParams(
            target_files=target_files,
            fmt=fmt,
            include_binary=profile.include_binary,
            binary_extensions=profile.binary_extensions,
            binary_max_mb=profile.binary_max_mb,
            verbose=False,
            include_header=bool(query and query.strip()),
            do_compress=do_compress,
            max_workers=int(_os.environ.get("ARACHNA_MAX_WORKERS", "1")),
            total_files=len(target_files),
            sections=sections,
            named_sections=named_sections,
            tokenizer=tokenizer,
            line_numbers=profile.line_numbers,
            root=root,
        )

    def _build_parts_from_params(self, params, max_tokens, tokenizer):
        if max_tokens == -1:
            parts = ["\n\n".join(s.strip() for s in params.sections if s.strip())]
            indices = [list(range(len(params.named_sections)))]
        else:
            parts, indices = pack_into_parts(params.sections, max_tokens, tokenizer=tokenizer)
        return parts, indices

    def assemble(self, profile, exclude, tokenizer, root, incremental, cache, verbose, query):
        from .gatherer_commands import _collect_pre_commands

        max_tokens = profile.max_tokens
        do_compress = profile.compress
        target_files, new_cache = self._resolve_target_files(
            profile, exclude, root, incremental, cache, query
        )
        pre_sections = _collect_pre_commands(profile.to_dict(), tokenizer, root)
        params = self._build_collect_params(
            target_files, profile, pre_sections, tokenizer, root, query
        )
        params.verbose = verbose
        if verbose and params.total_files > 100:
            print(f"  Collecting... 0/{params.total_files} files", file=sys.stderr)
        self._collect(params)
        if query and query.strip():
            params.named_sections = _filter_by_query(
                params.named_sections, query, graph_cache=self._graph_cache
            )
        parts, indices = self._build_parts_from_params(params, max_tokens, tokenizer)
        if verbose and do_compress:
            raw_tokens = sum(tokens for _name, _content, tokens in params.named_sections)
            _print_compress_stats(raw_tokens, sum(tokenizer(p) for p in parts))
        return params.named_sections, parts, indices, new_cache

    def _collect(self, params):
        if params.max_workers > 1 and params.total_files > 1:
            self._collect_parallel(params)
        else:
            self._collect_sequential(params)

    def _collect_parallel(self, params):
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            with ThreadPoolExecutor(max_workers=params.max_workers) as executor:
                futures = {
                    executor.submit(
                        _format_one_file,
                        fp,
                        params.fmt,
                        params.include_binary,
                        params.binary_extensions,
                        params.binary_max_mb,
                        params.verbose,
                        params.include_header,
                        params.do_compress,
                        params.line_numbers,
                        params.root,
                    ): idx
                    for idx, fp in enumerate(params.target_files)
                }
                results_map = {}
                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        results_map[futures[future]] = result
                    if params.verbose and params.total_files > 100 and len(results_map) % 100 == 0:
                        print(
                            f"  collected {len(results_map)}/{params.total_files} files...",
                            file=sys.stderr,
                        )
            for idx in range(len(params.target_files)):
                if idx in results_map:
                    fp_str, content, _ = results_map[idx]
                    tokens = params.tokenizer(content)
                    params.sections.append(content)
                    params.named_sections.append((fp_str, content, tokens))
        except ImportError:
            self._collect_sequential(params)

    def _collect_sequential(self, params):
        for idx, fp in enumerate(params.target_files):
            result = _format_one_file(
                fp,
                params.fmt,
                params.include_binary,
                params.binary_extensions,
                params.binary_max_mb,
                params.verbose,
                params.include_header,
                params.do_compress,
                params.line_numbers,
                params.root,
            )
            if result is not None:
                fp_str, content, _ = result
                tokens = params.tokenizer(content)
                params.sections.append(content)
                params.named_sections.append((fp_str, content, tokens))
            if params.verbose and params.total_files > 100 and (idx + 1) % 100 == 0:
                print(f"  collected {idx + 1}/{params.total_files} files...", file=sys.stderr)


class _RepoMapModeStrategy:
    def __init__(self):
        self._graph_cache = {}

    def assemble(self, p, e, t, r, i, c, v, q):
        return _assemble_in_memory(p, e, t, r, i, c, v, q, "repo-map", self._graph_cache)


class _HeadersModeStrategy:
    def __init__(self):
        self._graph_cache = {}

    def assemble(self, p, e, t, r, i, c, v, q):
        return _assemble_in_memory(p, e, t, r, i, c, v, q, "headers", self._graph_cache)


@functools.lru_cache(maxsize=1)
def get_mode_strategies():
    """Return cached mode strategies — single instance per process."""
    return {
        "full": _FullModeStrategy(),
        "repo-map": _RepoMapModeStrategy(),
        "headers": _HeadersModeStrategy(),
    }


def _build_in_memory_parts(named_sections, do_compress, max_tokens, tokenizer, verbose):
    sections = []
    raw_tokens = 0
    for _name, content, tokens in named_sections:
        raw_tokens += tokens
        sections.append(_compress(content) if do_compress and content.strip() else content)
    if max_tokens == -1:
        return (
            sections,
            ["\n\n".join(s.strip() for s in sections if s.strip())],
            [list(range(len(named_sections)))],
        )
    if verbose and do_compress:
        _print_compress_stats(raw_tokens, sum(tokenizer(s) for s in sections))
    parts, indices = split_sections(sections, max_tokens, separator="\n\n", tokenizer=tokenizer)
    return sections, parts, indices


def _assemble_in_memory(
    profile,
    exclude,
    tokenizer,
    root,
    incremental,
    cache,
    verbose,
    query,
    mode: CollectionMode,
    graph_cache=None,
):
    from .gatherer_files import _collect_named_sections

    if graph_cache is None:
        graph_cache = {}
    named_sections, new_cache = _collect_named_sections(
        profile,
        exclude,
        tokenizer,
        root,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
        include_header=bool(query and query.strip()) or mode == "headers",
        query=query,
        mode=mode,
        graph_cache=graph_cache,
    )
    _, parts, indices = _build_in_memory_parts(
        named_sections,
        profile.compress,
        profile.max_tokens,
        tokenizer,
        verbose,
    )
    return named_sections, parts, indices, new_cache
