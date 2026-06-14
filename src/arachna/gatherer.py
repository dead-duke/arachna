"""Content gatherer — collects files and runs commands.

Streaming pipeline for full mode:
1. Pre_commands run immediately, output goes to first part (compressed if needed).
2. Metadata pass: stat files, run query filter on filenames.
3. Streaming pass: read → format → compress → pack → flush when full.
   Memory: O(max_tokens + metadata), not O(total content).

Repo-map and headers modes stay in-memory — they need file content
for signature extraction and header generation before token counting.
Note: mode="headers" means mode="full" with dependency/export headers
prepended to each file section. It does NOT mean "headers only" —
for signatures-only output use mode="repo-map".

v3.5: Strategy pattern for mode dispatch — FullModeStrategy (streaming),
RepoMapModeStrategy (signatures), HeadersModeStrategy (dependency headers).
root parameter propagates through scan/collect/assemble chain.
"""

import contextlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .cache import get_changed_files, update_cache
from .compressor import compress as _compress
from .formatter import _generate_header, format_file_section, is_excluded, lang_for_path
from .gitignore import load_gitignore_patterns
from .runner import run_command
from .splitter import extract_signatures, split, split_sections
from .tokenizer import count_tokens


def _collect_pre_commands(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int],
) -> list[tuple[str, str, int]]:
    from .runner import run_pre_commands

    results = []
    commands = profile.get("pre_commands", [])
    if not commands:
        return results
    for cmd, output in run_pre_commands(commands):
        if output.strip():
            tokens = tokenizer(output)
            label = cmd if len(cmd) <= 50 else cmd[:47] + "..."
            results.append((f"pre: {label}", output, tokens))
    return results


def _scan_directories(
    profile: dict[str, Any],
    exclude: list[str],
    root: Path | None = None,
) -> list[Path]:
    """Scan directories from profile, relative to root (default: cwd)."""
    if root is None:
        root = Path.cwd()
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
    if fmt == "xml":
        return header + _format_xml_sigs(filepath, lang, sigs)
    elif fmt == "json":
        return header + _format_json_sigs(filepath, lang, sigs)
    else:
        return header + _format_markdown_sigs(filepath, lang, sigs)


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


def _format_markdown_sigs(filepath: Path, lang: str, sigs: str) -> str:
    fence_lang = lang if lang else ""
    return f"### {filepath}\n\n```{fence_lang}\n{sigs}\n```\n"


def _format_xml_sigs(filepath: Path, lang: str, sigs: str) -> str:
    lang_attr = f' language="{lang}"' if lang else ""
    return f'<file path="{filepath}"{lang_attr}>\n<![CDATA[\n{sigs}\n]]>\n</file>\n'


def _format_json_sigs(filepath: Path, lang: str, sigs: str) -> str:
    import json

    obj = {"path": str(filepath), "content": sigs}
    if lang:
        obj["language"] = lang
    return json.dumps(obj, ensure_ascii=False) + "\n"


def _collect_directory_sections(
    profile: dict[str, Any],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    incremental: bool = False,
    cache: dict[str, float] | None = None,
    verbose: bool = False,
    include_header: bool = False,
    mode: str = "full",
    root: Path | None = None,
) -> tuple[list[tuple[str, str, int]], dict[str, float] | None]:
    fmt = profile.get("section_format", "markdown")
    include_binary = profile.get("include_binary", False)
    binary_extensions = profile.get("binary_extensions")
    binary_max_mb = profile.get("binary_max_mb", 1.0)
    seen_files = _scan_directories(profile, exclude, root=root)
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


_import_graph_cache: dict[tuple, dict[str, list[str]]] = {}


def _collect_import_graph(named_sections: list[tuple[str, str, int]]) -> dict[str, list[str]]:
    cache_key = tuple((fp, hash(content) & 0xFFFFFFFF) for fp, content, _tokens in named_sections)
    if cache_key in _import_graph_cache:
        return _import_graph_cache[cache_key]

    graph: dict[str, list[str]] = {}
    for filepath, content, _tokens in named_sections:
        deps = _extract_deps_from_content(content)
        if deps is None:
            lang = lang_for_path(Path(filepath))
            header = _generate_header(Path(filepath), content, lang)
            deps = _extract_deps_from_content(header) or []
        graph[filepath] = deps

    if len(_import_graph_cache) > 128:
        _import_graph_cache.clear()
    _import_graph_cache[cache_key] = graph
    return graph


def _extract_deps_from_content(content: str) -> list[str] | None:
    for line in content.split("\n"):
        if line.startswith("deps: "):
            deps_str = line[6:]
            return [d.strip() for d in deps_str.split(",") if d.strip()]
    return None


def _score_files(
    named_sections: list[tuple[str, str, int]],
    query_words: list[str],
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
                exports_str = line[9:]
                for word in query_words:
                    if word in exports_str.lower():
                        score += 8
                break
        if score > 0:
            scores[filepath] = score

    graph = _collect_import_graph(named_sections)
    for filepath in scores:
        for dep in graph.get(filepath, []):
            for word in query_words:
                if word in dep.lower():
                    scores[filepath] += 5
    return scores


def _build_reverse_graph(
    graph: dict[str, list[str]],
) -> dict[str, list[str]]:
    reverse: dict[str, list[str]] = {}
    for fpath, deps in graph.items():
        for dep in deps:
            dep_basename = dep.split("/")[-1].split(".")[0]
            reverse.setdefault(dep_basename, []).append(fpath)
            reverse.setdefault(dep, []).append(fpath)
    return reverse


def _expand_import_chain(
    matched: set[str],
    reverse_graph: dict[str, list[str]],
    depth: int = 2,
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
) -> list[tuple[str, str, int]]:
    if not query or not query.strip():
        return named_sections

    query_words = query.lower().split()
    scores = _score_files(named_sections, query_words)
    if not scores:
        return (
            [s for s in named_sections if s[0].startswith("pre: ")] if include_pre_commands else []
        )

    matched = set(scores.keys())
    graph = _collect_import_graph(named_sections)
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
        fname_lower = fp.name.lower()
        for word in query_words:
            if word in fname_lower:
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


# ── Strategy pattern for mode dispatch ───────────────────────────


class _FullModeStrategy:
    """Streaming mode — reads and packs files on the fly, O(max_tokens) memory."""

    def assemble(
        self,
        profile: dict[str, Any],
        exclude: list[str],
        tokenizer: Callable[[str], int],
        incremental: bool,
        cache: dict[str, float] | None,
        verbose: bool,
        query: str | None,
        root: Path | None = None,
    ) -> tuple[list[tuple[str, str, int]], list[str], list[list[int]], dict[str, float]]:
        from .splitter import pack_into_parts

        do_compress = profile.get("compress", False)
        max_tokens = profile.get("max_tokens", 16000)
        include_header = bool(query and query.strip())

        filepaths = _scan_directories(profile, exclude, root=root)
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

        pre_sections = _collect_pre_commands(profile, tokenizer)
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

        for fp in target_files:
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
                continue
            if do_compress:
                section = _compress(section)
            tokens = tokenizer(section)
            sections.append(section)
            named_sections.append((str(fp), section, tokens))

        parts, indices = pack_into_parts(sections, max_tokens, tokenizer=tokenizer)

        if verbose and do_compress:
            raw_tokens = sum(tokens for _name, _content, tokens in named_sections)
            comp_tokens = sum(tokenizer(p) for p in parts)
            _print_compress_stats(raw_tokens, comp_tokens)

        return named_sections, parts, indices, new_cache


class _RepoMapModeStrategy:
    """In-memory mode — extracts signatures, O(total content) memory."""

    def assemble(
        self,
        profile: dict[str, Any],
        exclude: list[str],
        tokenizer: Callable[[str], int],
        incremental: bool,
        cache: dict[str, float] | None,
        verbose: bool,
        query: str | None,
        root: Path | None = None,
    ) -> tuple[list[tuple[str, str, int]], list[str], list[list[int]], dict[str, float]]:
        return _assemble_in_memory(
            profile, exclude, tokenizer, incremental, cache, verbose, query, "repo-map", root=root
        )


class _HeadersModeStrategy:
    """In-memory mode — includes dependency/export headers, O(total content) memory."""

    def assemble(
        self,
        profile: dict[str, Any],
        exclude: list[str],
        tokenizer: Callable[[str], int],
        incremental: bool,
        cache: dict[str, float] | None,
        verbose: bool,
        query: str | None,
        root: Path | None = None,
    ) -> tuple[list[tuple[str, str, int]], list[str], list[list[int]], dict[str, float]]:
        return _assemble_in_memory(
            profile, exclude, tokenizer, incremental, cache, verbose, query, "headers", root=root
        )


_MODE_STRATEGIES = {
    "full": _FullModeStrategy(),
    "repo-map": _RepoMapModeStrategy(),
    "headers": _HeadersModeStrategy(),
}


def _assemble_in_memory(
    profile: dict[str, Any],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    incremental: bool,
    cache: dict[str, float] | None,
    verbose: bool,
    query: str | None,
    mode: str,
    root: Path | None = None,
) -> tuple[list[tuple[str, str, int]], list[str], list[list[int]], dict[str, float]]:
    do_compress = profile.get("compress", False)
    max_tokens = profile.get("max_tokens", 16000)
    include_header = bool(query and query.strip()) or mode == "headers"

    named_sections, new_cache = _collect_named_sections(
        profile,
        exclude,
        tokenizer=tokenizer,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
        include_header=include_header,
        query=query,
        mode=mode,
        root=root,
    )
    sections = []
    raw_tokens = 0
    for _name, content, tokens in named_sections:
        raw_tokens += tokens
        if do_compress and content.strip():
            sections.append(_compress(content))
        else:
            sections.append(content)
    if verbose and do_compress:
        comp_tokens = sum(tokenizer(s) for s in sections)
        _print_compress_stats(raw_tokens, comp_tokens)
    parts, indices = split_sections(sections, max_tokens, separator="\n\n", tokenizer=tokenizer)
    return named_sections, parts, indices, new_cache


def _collect_named_sections(
    profile: dict[str, Any],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    incremental: bool = False,
    cache: dict[str, float] | None = None,
    verbose: bool = False,
    include_header: bool = False,
    query: str | None = None,
    mode: str = "full",
    root: Path | None = None,
) -> tuple[list[tuple[str, str, int]], dict[str, float]]:
    named_sections = []
    named_sections.extend(_collect_pre_commands(profile, tokenizer))
    dir_sections, new_cache = _collect_directory_sections(
        profile,
        exclude,
        tokenizer,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
        include_header=include_header,
        mode=mode,
        root=root,
    )
    named_sections.extend(dir_sections)
    named_sections.extend(
        _collect_file_sections(
            profile,
            exclude,
            tokenizer,
            verbose=verbose,
            include_header=include_header,
            mode=mode,
        )
    )
    if query and query.strip():
        named_sections = _filter_by_query(named_sections, query)
    return named_sections, new_cache


def _assemble_command_content(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int],
    query: str | None = None,
    mode: str = "full",
) -> tuple[list[tuple[str, str, int]], list[str], list[list[int]], dict[str, float]]:
    command = profile["command"]
    do_compress = profile.get("compress", False)
    split_mode = profile.get("split_mode", "by_file")
    split_marker = profile.get("split_marker", "\n\n")
    max_tokens = profile.get("max_tokens", 16000)
    raw_content = gather_command(command)
    if do_compress and raw_content.strip():
        raw_content = _compress(raw_content)
    named_sections = [("command output", raw_content, tokenizer(raw_content))]
    parts = split(raw_content, max_tokens, split_mode, split_marker, tokenizer=tokenizer)
    indices = [[0] for _ in parts]
    return named_sections, parts, indices, {}


def _assemble_file_content(
    profile: dict[str, Any],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    incremental: bool = False,
    cache: dict[str, float] | None = None,
    verbose: bool = False,
    query: str | None = None,
    mode: str = "full",
    root: Path | None = None,
) -> tuple[list[tuple[str, str, int]], list[str], list[list[int]], dict[str, float]]:
    strategy = _MODE_STRATEGIES.get(mode, _MODE_STRATEGIES["full"])
    return strategy.assemble(
        profile, exclude, tokenizer, incremental, cache, verbose, query, root=root
    )


def _assemble_content(
    profile: dict[str, Any],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    incremental: bool = False,
    cache: dict[str, float] | None = None,
    verbose: bool = False,
    query: str | None = None,
    mode: str = "full",
    root: Path | None = None,
) -> tuple[list[tuple[str, str, int]], list[str], list[list[int]], dict[str, float]]:
    if profile.get("command"):
        if profile.get("directories") or profile.get("files"):
            print(
                "  Warning: profile has both 'command' and 'directories'/'files'. Using 'command', ignoring directories and files."
            )
        return _assemble_command_content(profile, tokenizer, query=query, mode=mode)
    return _assemble_file_content(
        profile,
        exclude,
        tokenizer,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
        query=query,
        mode=mode,
        root=root,
    )


def _apply_repo_map_to_sections(
    sections: list,
    snapshot_id: str,
    to_snapshot_id: str | None,
    profile: dict,
    root: Path | None = None,
) -> list:
    from .formatter import lang_for_path
    from .store import load_snapshot

    manifest = load_snapshot(snapshot_id, root=root)
    snapshot_files = manifest.get("files", {})
    to_files = None
    if to_snapshot_id:
        to_manifest = load_snapshot(to_snapshot_id, root=root)
        to_files = to_manifest.get("files", {})
    result = []
    for s in sections:
        if s.type in ("header",) or not s.path:
            result.append(s)
            continue
        lang = lang_for_path(Path(s.path))
        if s.type == "modified":
            old_content = _read_file_from_store(s.path, snapshot_files, root=root)
            new_content = (
                _read_file_from_disk(s.path)
                if to_files is None
                else _read_file_from_store(s.path, to_files, root=root)
            )
            if old_content is not None and new_content is not None:
                old_blocks = _parse_blocks_dispatch(old_content, lang)
                new_blocks = _parse_blocks_dispatch(new_content, lang)
                s.content = _format_repo_map_diff(s.path, lang, old_blocks, new_blocks)
        elif s.type == "added":
            new_content = (
                _read_file_from_disk(s.path)
                if to_files is None
                else _read_file_from_store(s.path, to_files, root=root)
            )
            if new_content is not None:
                blocks = _parse_blocks_dispatch(new_content, lang)
                s.content = _format_repo_map_added(s.path, lang, blocks)
        elif s.type == "deleted":
            old_content = _read_file_from_store(s.path, snapshot_files, root=root)
            if old_content is not None:
                blocks = _parse_blocks_dispatch(old_content, lang)
                sig_lines = [f"  {sig}" for sig, _body in blocks.values()]
                if sig_lines:
                    s.content = (
                        f"### {s.path}\n\n[DELETED]\n\nRemoved signatures:\n"
                        + "\n".join(sig_lines)
                        + "\n"
                    )
        result.append(s)
    return result


def _parse_blocks_dispatch(text: str, lang: str) -> dict[str, tuple[str, str]]:
    from .differ_structural import _parse_c_like_blocks, _parse_python_blocks, _parse_script_blocks
    from .formatter import C_LIKE_LANGS, SCRIPT_LANGS

    if lang == "python":
        blocks = _parse_python_blocks(text)
        return blocks if blocks is not None else {}
    elif lang in C_LIKE_LANGS or lang == "gdscript":
        return _parse_c_like_blocks(text, lang)
    elif lang in SCRIPT_LANGS:
        return _parse_script_blocks(text)
    return {}


def _read_file_from_store(path: str, files: dict, root: Path | None = None) -> str | None:
    from .store import read_object

    for fpath, hash_spec in files.items():
        if fpath == path:
            obj_hash = hash_spec[7:]
            try:
                return read_object(obj_hash, root=root).decode("utf-8")
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


def _format_repo_map_diff(path: str, lang: str, old_blocks: dict, new_blocks: dict) -> str:
    import hashlib

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
            body_changed = (
                hashlib.sha256(old_body.encode()).hexdigest()
                != hashlib.sha256(new_body.encode()).hexdigest()
            )
            if sig_changed:
                parts.append(f"~ {old_sig}\n  -> {new_sig}\n")
            elif body_changed:
                parts.append(f"  {old_sig}  (body changed)\n")
    return "".join(parts) if len(parts) > 1 else ""


def _format_repo_map_added(path: str, lang: str, blocks: dict) -> str:
    parts = [f"### {path}\n"]
    for _name, (sig, _body) in blocks.items():
        parts.append(f"+ {sig}\n")
    return "".join(parts) if len(parts) > 1 else ""


def gather_files(
    profile: dict[str, Any],
    verbose: bool = False,
    tokenizer: Callable[[str], int] | None = None,
    root: Path | None = None,
) -> list[str]:
    tk = tokenizer if tokenizer is not None else count_tokens
    exclude = _get_exclude_patterns(profile, root=root)
    sections, _ = _collect_named_sections(
        profile, exclude, tokenizer=tk, verbose=verbose, root=root
    )
    return [content for _, content, _ in sections]


def gather_command(cmd: str) -> str:
    return run_command(cmd, allow_file_args=True)


def dry_run(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int] | None = None,
    query: str | None = None,
    mode: str = "full",
    root: Path | None = None,
) -> dict:
    tk = tokenizer if tokenizer is not None else count_tokens
    exclude = _get_exclude_patterns(profile, root=root)
    max_tokens = profile.get("max_tokens", 16000)
    name_tmpl = profile.get("name_template", "chat")
    named_sections, parts, indices, _ = _assemble_content(
        profile,
        exclude,
        tk,
        incremental=False,
        cache=None,
        verbose=False,
        query=query,
        mode=mode,
        root=root,
    )
    part_list = []
    for i, (content, idxs) in enumerate(zip(parts, indices, strict=True), 1):
        part_sections = [
            (named_sections[j][0], named_sections[j][2]) for j in idxs if j < len(named_sections)
        ]
        total_tokens = tk(content)
        part_list.append({"part_num": i, "sections": part_sections, "total_tokens": total_tokens})
    return {"name_tmpl": name_tmpl, "max_tokens": max_tokens, "parts": part_list}


def _get_exclude_patterns(profile: dict[str, Any], root: Path | None = None) -> list[str]:
    if root is None:
        root = Path.cwd()
    exclude = list(profile.get("exclude_patterns", []))
    if profile.get("use_gitignore", True):
        exclude.extend(load_gitignore_patterns(root))
    return exclude
