"""Content gatherer - collects files and runs commands.

v4.0.0: Moved to domain/ package. All imports from domain/.
- Format dispatch via mapping (no if/elif/else chains)
- Strategy lazy-init (not import-time instantiation)
- Import graph cache encapsulated in strategy instances (not global)
"""

import contextlib
import os as _os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .cache import get_changed_files, update_cache
from .compressor import compress as _compress
from .formatter import _generate_header, format_file_section, is_excluded, lang_for_path
from .gitignore import load_gitignore_patterns
from .runner import run_command, run_pre_commands
from .splitter import extract_signatures, split, split_sections
from .tokenizer import count_tokens


def _collect_pre_commands(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int],
    root: Path,
) -> list[tuple[str, str, int]]:
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


# Format dispatch for repo-map signatures


def _format_sigs_markdown(filepath: Path, lang: str, sigs: str) -> str:
    return f"### {filepath}\n\n```{lang if lang else ''}\n{sigs}\n```\n"


def _format_sigs_xml(filepath: Path, lang: str, sigs: str) -> str:
    lang_attr = f' language="{lang}"' if lang else ""
    return f'<file path="{filepath}"{lang_attr}>\n<![CDATA[\n{sigs}\n]]>\n</file>\n'


def _format_sigs_json(filepath: Path, lang: str, sigs: str) -> str:
    import json

    obj = {"path": str(filepath), "content": sigs}
    if lang:
        obj["language"] = lang
    return json.dumps(obj, ensure_ascii=False) + "\n"


_SIGS_FORMATTERS = {
    "markdown": _format_sigs_markdown,
    "xml": _format_sigs_xml,
    "json": _format_sigs_json,
}


def _apply_repo_map_to_section(
    filepath: Path,
    section: str,
    raw_text: str | None,
    lang: str,
    fmt: str,
    include_header: bool,
    header: str = "",
) -> str:
    if raw_text is None:
        return section
    sigs = extract_signatures(raw_text, lang)
    if not header and include_header:
        header = _generate_header(filepath, raw_text, lang)
    formatter = _SIGS_FORMATTERS.get(fmt, _format_sigs_markdown)
    return header + formatter(filepath, lang, sigs)


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


# Query pipeline — pure functions, no global state


def _collect_import_graph(
    named_sections: list[tuple[str, str, int]], graph_cache: dict
) -> dict[str, list[str]]:
    cache_key = tuple((fp, hash(content) & 0xFFFFFFFF) for fp, content, _tokens in named_sections)
    if cache_key in graph_cache:
        return graph_cache[cache_key]
    graph: dict[str, list[str]] = {}
    for filepath, content, _tokens in named_sections:
        deps = _extract_deps_from_content(content)
        if deps is None:
            lang = lang_for_path(Path(filepath))
            header = _generate_header(Path(filepath), content, lang)
            deps = _extract_deps_from_content(header) or []
        graph[filepath] = deps
    if len(graph_cache) > 128:
        graph_cache.clear()
    graph_cache[cache_key] = graph
    return graph


def _extract_deps_from_content(content: str) -> list[str] | None:
    for line in content.split("\n"):
        if line.startswith("deps: "):
            return [d.strip() for d in line[6:].split(",") if d.strip()]
    return None


def _score_files(
    named_sections: list[tuple[str, str, int]], query_words: list[str], graph_cache: dict
) -> dict[str, int]:
    scores: dict[str, int] = {}
    for filepath, content, _tokens in named_sections:
        if filepath.startswith("pre: "):
            continue
        score = 0
        fname_lower = Path(filepath).name.lower()
        content_lower = content.lower()
        for word in query_words:
            if word in fname_lower:
                score += 10
            if word in content_lower:
                score += 3
        for line in content.split("\n"):
            if line.startswith("exports: "):
                for word in query_words:
                    if word in line[9:].lower():
                        score += 8
                break
        if score > 0:
            scores[filepath] = score
    graph = _collect_import_graph(named_sections, graph_cache)
    for filepath in scores:
        for dep in graph.get(filepath, []):
            for word in query_words:
                if word in dep.lower():
                    scores[filepath] += 5
    return scores


def _build_reverse_graph(graph: dict[str, list[str]]) -> dict[str, list[str]]:
    reverse: dict[str, list[str]] = {}
    for fpath, deps in graph.items():
        for dep in deps:
            dep_basename = dep.split("/")[-1].split(".")[0]
            reverse.setdefault(dep_basename, []).append(fpath)
            reverse.setdefault(dep, []).append(fpath)
    return reverse


def _expand_import_chain(
    matched: set[str], reverse_graph: dict[str, list[str]], depth: int = 2
) -> set[str]:
    result = set(matched)
    for _ in range(depth):
        new_matches: set[str] = set()
        for fpath in result:
            basename = Path(fpath).name.split(".")[0]
            for importer in reverse_graph.get(basename, []):
                if importer not in result:
                    new_matches.add(importer)
            for importer in reverse_graph.get(fpath, []):
                if importer not in result:
                    new_matches.add(importer)
        if not new_matches:
            break
        result |= new_matches
    return result


def _filter_by_query(
    named_sections: list[tuple[str, str, int]],
    query: str,
    include_pre_commands: bool = False,
    graph_cache: dict | None = None,
) -> list[tuple[str, str, int]]:
    if graph_cache is None:
        graph_cache = {}
    if not query or not query.strip():
        return named_sections
    query_words = query.lower().split()
    scores = _score_files(named_sections, query_words, graph_cache)
    if not scores:
        return (
            [s for s in named_sections if s[0].startswith("pre: ")] if include_pre_commands else []
        )
    matched = set(scores.keys())
    graph = _collect_import_graph(named_sections, graph_cache)
    reverse_graph = _build_reverse_graph(graph)
    matched = _expand_import_chain(matched, reverse_graph)
    result = []
    for section in named_sections:
        if section[0].startswith("pre: "):
            if include_pre_commands:
                result.append(section)
        elif section[0] in matched:
            result.append(section)
    return result


def _filter_filenames_by_query(filepaths: list[Path], query: str) -> list[Path]:
    if not query or not query.strip():
        return filepaths
    query_words = query.lower().split()
    result = []
    for fp in filepaths:
        for word in query_words:
            if word in fp.name.lower():
                result.append(fp)
                break
    return result


def _get_profile_files(profile: dict[str, Any], exclude: list[str]) -> list[Path]:
    filepaths = []
    for filepath_str in profile.get("files", []):
        filepath = Path(filepath_str)
        if not filepath.is_file():
            continue
        if is_excluded(filepath, exclude):
            continue
        filepaths.append(filepath)
    return filepaths


def _print_compress_stats(raw_tokens: int, comp_tokens: int):
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


# Strategy classes with encapsulated import graph cache


class _FullModeStrategy:
    def __init__(self):
        self._graph_cache: dict = {}

    def assemble(
        self,
        profile: dict[str, Any],
        exclude: list[str],
        tokenizer: Callable[[str], int],
        root: Path,
        incremental: bool,
        cache: dict[str, float] | None,
        verbose: bool,
        query: str | None,
    ) -> tuple[list[tuple[str, str, int]], list[str], list[list[int]], dict[str, float]]:
        from .splitter import pack_into_parts

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
            print(f"  Collecting... 0/{total_files} files", file=__import__("sys").stderr)
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
                            file=__import__("sys").stderr,
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
                    f"  collected {idx + 1}/{total_files} files...", file=__import__("sys").stderr
                )


class _RepoMapModeStrategy:
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


def _assemble_command_content(profile, tokenizer, root, query=None, mode="full"):
    command = profile["command"]
    do_compress = profile.get("compress", False)
    split_mode = profile.get("split_mode", "by_file")
    split_marker = profile.get("split_marker", "\n\n")
    max_tokens = profile.get("max_tokens", 16000)
    raw_content = gather_command(command, root=root)
    if do_compress and raw_content.strip():
        raw_content = _compress(raw_content)
    named_sections = [("command output", raw_content, tokenizer(raw_content))]
    parts = split(raw_content, max_tokens, split_mode, split_marker, tokenizer=tokenizer)
    indices = [[0] for _ in parts]
    return named_sections, parts, indices, {}


def _assemble_file_content(
    profile,
    exclude,
    tokenizer,
    root,
    incremental=False,
    cache=None,
    verbose=False,
    query=None,
    mode="full",
):
    strategies = _get_mode_strategies()
    strategy = strategies.get(mode, strategies["full"])
    return strategy.assemble(profile, exclude, tokenizer, root, incremental, cache, verbose, query)


def _assemble_content(
    profile,
    exclude,
    tokenizer,
    root,
    incremental=False,
    cache=None,
    verbose=False,
    query=None,
    mode="full",
):
    if profile.get("command"):
        if profile.get("directories") or profile.get("files"):
            print(
                "  Warning: profile has both 'command' and 'directories'/'files'. Using 'command', ignoring directories and files."
            )
        return _assemble_command_content(profile, tokenizer, root, query=query, mode=mode)
    return _assemble_file_content(
        profile,
        exclude,
        tokenizer,
        root,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
        query=query,
        mode=mode,
    )


def gather_files(profile, root, verbose=False, tokenizer=None):
    tk = tokenizer if tokenizer is not None else count_tokens
    exclude = _get_exclude_patterns(profile, root=root)
    sections, _ = _collect_named_sections(
        profile, exclude, tokenizer=tk, root=root, verbose=verbose
    )
    return [content for _, content, _ in sections]


def gather_command(cmd, root):
    return run_command(cmd, root=root, allow_file_args=True)


def dry_run(profile, root, tokenizer=None, query=None, mode="full"):
    tk = tokenizer if tokenizer is not None else count_tokens
    exclude = _get_exclude_patterns(profile, root=root)
    max_tokens = profile.get("max_tokens", 16000)
    name_tmpl = profile.get("name_template", "chat")
    named_sections, parts, indices, _ = _assemble_content(
        profile,
        exclude,
        tk,
        root,
        incremental=False,
        cache=None,
        verbose=False,
        query=query,
        mode=mode,
    )
    part_list = []
    for i, (content, idxs) in enumerate(zip(parts, indices, strict=True), 1):
        part_sections = [
            (named_sections[j][0], named_sections[j][2]) for j in idxs if j < len(named_sections)
        ]
        total_tokens = tk(content)
        part_list.append({"part_num": i, "sections": part_sections, "total_tokens": total_tokens})
    return {"name_tmpl": name_tmpl, "max_tokens": max_tokens, "parts": part_list}


def _get_exclude_patterns(profile, root):
    exclude = list(profile.get("exclude_patterns", []))
    if profile.get("use_gitignore", True):
        exclude.extend(load_gitignore_patterns(root))
    return exclude
