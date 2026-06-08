"""Content gatherer — collects files and runs commands."""

import contextlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .cache import get_changed_files, update_cache
from .compressor import compress
from .formatter import _generate_header, format_file_section, is_excluded, lang_for_path
from .gitignore import load_gitignore_patterns
from .runner import run_command
from .splitter import extract_signatures, split, split_sections
from .tokenizer import count_tokens


def _collect_pre_commands(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int],
) -> list[tuple[str, str, int]]:
    """Run pre_commands and return (label, output, tokens) tuples.

    Pre_commands are shell commands defined in the profile that run
    before file collection (e.g. tree, git log). Their output is
    included as named sections in the collected context.
    """
    results = []
    for cmd in profile.get("pre_commands", []):
        output = run_command(cmd)
        if output.strip():
            tokens = tokenizer(output)
            label = cmd if len(cmd) <= 50 else cmd[:47] + "..."
            results.append((f"pre: {label}", output, tokens))
    return results


def _scan_directories(
    profile: dict[str, Any],
    exclude: list[str],
) -> list[Path]:
    """Scan directories for matching files, return sorted Path list.

    Symlinks are skipped with a warning to prevent path traversal
    outside the project root.
    """
    seen = []
    for directory in profile.get("directories", []):
        dir_path = Path(directory)
        if dir_path.is_symlink():
            print(f"  Warning: skipping symlink directory: {dir_path}")
            continue
        for pattern in profile.get("patterns", ["*"]):
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
) -> str:
    """Apply repo-map transformation to a formatted section.

    Reads raw text, extracts signatures, and reformats as signature-only
    output. If raw_text is None (could not be read), returns the original
    section unchanged.

    Args:
        filepath: Path to the source file.
        section: Already-formatted section string (markdown/xml/json).
        raw_text: Raw file content, or None if unreadable.
        lang: Detected language.
        fmt: Output format.
        include_header: Whether to include dependency/export headers.

    Returns:
        Repo-map formatted section, or original section if raw_text is None.
    """
    if raw_text is None:
        return section

    sigs = extract_signatures(raw_text, lang)
    header = ""
    if include_header:
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
    """Format a list of file paths into (path, content, tokens) tuples.

    Shared by _format_scanned_files and _collect_specific_files.
    For repo-map mode, reads raw text first, applies extract_signatures,
    then formats only the signatures.

    Args:
        filepaths: List of Path objects to format.
        tokenizer: Token counting function.
        fmt: Output format — "markdown", "xml", or "json".
        include_binary: Whether to include binary files as base64.
        binary_extensions: Whitelist of binary extensions, or None for all.
        binary_max_mb: Maximum binary file size in MB.
        verbose: Whether to print skip reasons.
        include_header: Whether to prepend dependency/export headers.
        mode: Collection mode — "full", "headers", or "repo-map".

    Returns:
        List of (filepath_str, formatted_content, token_count) tuples.
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
                section = _apply_repo_map_to_section(
                    filepath, section, raw_text, lang, fmt, include_header
                )

            tokens = tokenizer(section)
            results.append((str(filepath), section, tokens))
    return results


def _format_scanned_files(
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
    """Format scanned files into (path, content, tokens) tuples.

    Delegates to _format_file_list.
    """
    return _format_file_list(
        filepaths,
        tokenizer,
        fmt=fmt,
        include_binary=include_binary,
        binary_extensions=binary_extensions,
        binary_max_mb=binary_max_mb,
        verbose=verbose,
        include_header=include_header,
        mode=mode,
    )


# ── Repo-map formatting helpers ────────────────────────────────────


def _format_markdown_sigs(filepath: Path, lang: str, sigs: str) -> str:
    """Format signatures as markdown code block."""
    fence_lang = lang if lang else ""
    return f"### {filepath}\n\n```{fence_lang}\n{sigs}\n```\n"


def _format_xml_sigs(filepath: Path, lang: str, sigs: str) -> str:
    """Format signatures as XML."""
    lang_attr = f' language="{lang}"' if lang else ""
    return f'<file path="{filepath}"{lang_attr}>\n<![CDATA[\n{sigs}\n]]>\n</file>\n'


def _format_json_sigs(filepath: Path, lang: str, sigs: str) -> str:
    """Format signatures as JSON."""
    import json

    obj = {"path": str(filepath), "content": sigs}
    if lang:
        obj["language"] = lang
    return json.dumps(obj, ensure_ascii=False) + "\n"


# ── End repo-map formatting ────────────────────────────────────────


def _collect_directory_sections(
    profile: dict[str, Any],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    incremental: bool = False,
    cache: dict[str, float] | None = None,
    verbose: bool = False,
    include_header: bool = False,
    mode: str = "full",
) -> tuple[list[tuple[str, str, int]], dict[str, float] | None]:
    """Collect sections from directory scans with optional incremental logic.

    Returns (sections, updated_cache).
    """
    fmt = profile.get("section_format", "markdown")
    include_binary = profile.get("include_binary", False)
    binary_extensions = profile.get("binary_extensions")
    binary_max_mb = profile.get("binary_max_mb", 1.0)

    seen_files = _scan_directories(profile, exclude)

    if incremental and cache is not None:
        changed, new, deleted = get_changed_files(seen_files, cache)
        target_files = changed + new
        # Explicitly remove deleted files from cache
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
    """Collect sections from explicitly listed files."""
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


# ── Query filtering ────────────────────────────────────────────────


def _collect_import_graph(
    named_sections: list[tuple[str, str, int]],
) -> dict[str, list[str]]:
    """Build {filepath: [imported_modules]} dict from section headers.

    Parses header deps from each section to build the import graph
    used by _filter_by_query for import chain analysis.
    """
    graph: dict[str, list[str]] = {}
    for filepath, content, _tokens in named_sections:
        lang = lang_for_path(Path(filepath))
        header = _generate_header(Path(filepath), content, lang)
        if not header:
            graph[filepath] = []
            continue
        for line in header.split("\n"):
            if line.startswith("deps: "):
                deps_str = line[6:]
                deps = [d.strip() for d in deps_str.split(",") if d.strip()]
                graph[filepath] = deps
                break
        else:
            graph[filepath] = []
    return graph


def _filter_by_query(
    named_sections: list[tuple[str, str, int]],
    query: str,
) -> list[tuple[str, str, int]]:
    """Filter named_sections by query relevance.

    Scoring algorithm:
    - +10: query word in filename (e.g. "auth" matches auth.py)
    - +8: query word in exports (function/class names from header)
    - +5: query word in imports (dependencies from header)
    - +3: query word in file content

    Files with score > 0 are included. Files that import matched
    files are also included via import chain (max depth 2).

    Pre_commands sections (pre: ...) always pass through unfiltered.

    Args:
        named_sections: List of (path, content, tokens) tuples.
        query: Space-separated query words.

    Returns:
        Filtered list preserving original order.
    """
    if not query or not query.strip():
        return named_sections

    query_words = query.lower().split()
    graph = _collect_import_graph(named_sections)

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

        lang = lang_for_path(Path(filepath))
        header = _generate_header(Path(filepath), content, lang)
        for line in header.split("\n"):
            if line.startswith("exports: "):
                exports_str = line[9:]
                for word in query_words:
                    if word in exports_str.lower():
                        score += 8
                break

        for dep in graph.get(filepath, []):
            for word in query_words:
                if word in dep.lower():
                    score += 5

        if score > 0:
            scores[filepath] = score

    matched = set(scores.keys())
    reverse: dict[str, list[str]] = {}
    for fpath, deps in graph.items():
        for dep in deps:
            dep_basename = dep.split("/")[-1].split(".")[0]
            reverse.setdefault(dep_basename, []).append(fpath)
            reverse.setdefault(dep, []).append(fpath)

    for _depth in range(2):
        new_matches: set[str] = set()
        for fpath in matched:
            basename = Path(fpath).name.split(".")[0]
            for importer in reverse.get(basename, []):
                if importer not in matched:
                    new_matches.add(importer)
            for importer in reverse.get(fpath, []):
                if importer not in matched:
                    new_matches.add(importer)
        matched |= new_matches
        if not new_matches:
            break

    result = []
    for section in named_sections:
        if section[0].startswith("pre: ") or section[0] in matched:
            result.append(section)
    return result


# ── End query filtering ────────────────────────────────────────────


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
) -> tuple[list[tuple[str, str, int]], dict[str, float]]:
    """Collect all named sections from pre_commands, directories, and files.

    Returns (named_sections, updated_cache).
    """
    named_sections = []

    # Pre-commands (never affected by repo-map)
    named_sections.extend(_collect_pre_commands(profile, tokenizer))

    # Directories (with incremental logic, repo-map applied at format level)
    dir_sections, new_cache = _collect_directory_sections(
        profile,
        exclude,
        tokenizer,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
        include_header=include_header,
        mode=mode,
    )
    named_sections.extend(dir_sections)

    # Specific files (repo-map applied at format level)
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

    # Apply query filtering if query is provided
    if query and query.strip():
        named_sections = _filter_by_query(named_sections, query)

    return named_sections, new_cache


def _assemble_command_content(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int],
    query: str | None = None,
    mode: str = "full",
) -> tuple[list[tuple[str, str, int]], list[str], dict[str, float]]:
    """Assemble content from a command source.

    Query and mode parameters are accepted for API symmetry with
    _assemble_file_content but are not applied to command output
    (command-based profiles produce a single section).

    Returns (named_sections, parts, empty_cache).
    """
    command = profile["command"]
    do_compress = profile.get("compress", False)
    split_mode = profile.get("split_mode", "by_file")
    split_marker = profile.get("split_marker", "\n\n")
    max_tokens = profile.get("max_tokens", 16000)

    raw_content = gather_command(command)
    if do_compress and raw_content.strip():
        raw_content = compress(raw_content)
    named_sections = [("command output", raw_content, tokenizer(raw_content))]
    parts = split(raw_content, max_tokens, split_mode, split_marker, tokenizer=tokenizer)
    return named_sections, parts, {}


def _assemble_file_content(
    profile: dict[str, Any],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    incremental: bool = False,
    cache: dict[str, float] | None = None,
    verbose: bool = False,
    query: str | None = None,
    mode: str = "full",
) -> tuple[list[tuple[str, str, int]], list[str], dict[str, float]]:
    """Assemble content from directories, files, and pre_commands.

    Pipeline: collect sections → filter by query → compress → split.

    Returns (named_sections, parts, updated_cache).
    """
    do_compress = profile.get("compress", False)
    max_tokens = profile.get("max_tokens", 16000)

    # Headers auto-enabled when query is used
    include_header = bool(query and query.strip()) or mode == "headers"

    # Step 1: Collect all named sections
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
    )

    # Step 2: Build list of section content strings with optional compression
    sections = []
    for _name, content, _tokens in named_sections:
        if do_compress and content.strip():
            sections.append(compress(content))
        else:
            sections.append(content)

    # Step 3: Compression stats
    if verbose and do_compress:
        raw_tokens = sum(tokens for _name, _content, tokens in named_sections)
        comp_tokens = sum(tokenizer(s) for s in sections)
        if raw_tokens > 0:
            pct = (raw_tokens - comp_tokens) / raw_tokens * 100
            print(f"  Compressed: ~{raw_tokens} -> ~{comp_tokens} tokens (-{pct:.0f}%)")

    # Step 4: Pack sections densely into token-limited parts
    parts = split_sections(sections, max_tokens, separator="\n\n", tokenizer=tokenizer)

    return named_sections, parts, new_cache


def _assemble_content(
    profile: dict[str, Any],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    incremental: bool = False,
    cache: dict[str, float] | None = None,
    verbose: bool = False,
    query: str | None = None,
    mode: str = "full",
) -> tuple[list[tuple[str, str, int]], list[str], dict[str, float]]:
    """Assemble raw content from profile and split into token-limited parts.

    Dispatches to _assemble_command_content for command-based profiles
    or _assemble_file_content for directory/file-based profiles.

    Returns (named_sections, parts, updated_cache).
    """
    if profile.get("command"):
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
    )


def _apply_repo_map_to_sections(
    sections: list,
    snapshot_id: str,
    to_snapshot_id: str | None,
    profile: dict,
) -> list:
    """Apply repo-map diff transformation to a list of DiffSections.

    Single shared pipeline for repo-map diff — used by watch.py,
    differ_structural, and cli_watch.

    Reads full source from store/disk, parses into named blocks,
    and formats repo-map output (signatures + change markers).

    Args:
        sections: List of DiffSection from watcher.compute_diff().
        snapshot_id: Source snapshot ID.
        to_snapshot_id: Target snapshot ID, or None for current disk.
        profile: Profile dict.

    Returns:
        List of DiffSection with repo-map formatted content.
    """
    from .formatter import lang_for_path
    from .store import load_snapshot

    manifest = load_snapshot(snapshot_id)
    snapshot_files = manifest.get("files", {})
    to_files = None
    if to_snapshot_id:
        to_manifest = load_snapshot(to_snapshot_id)
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
                old_blocks = _parse_blocks_dispatch(old_content, lang)
                new_blocks = _parse_blocks_dispatch(new_content, lang)
                s.content = _format_repo_map_diff(s.path, lang, old_blocks, new_blocks)
        elif s.type == "added":
            new_content = (
                _read_file_from_disk(s.path)
                if to_files is None
                else _read_file_from_store(s.path, to_files)
            )
            if new_content is not None:
                blocks = _parse_blocks_dispatch(new_content, lang)
                s.content = _format_repo_map_added(s.path, lang, blocks)
        elif s.type == "deleted":
            old_content = _read_file_from_store(s.path, snapshot_files)
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
    """Parse source into named blocks — dispatches by language."""
    from .differ_structural import _parse_c_like_blocks, _parse_python_blocks, _parse_script_blocks
    from .formatter import C_LIKE_LANGS, SCRIPT_LANGS

    if lang == "python":
        return _parse_python_blocks(text)
    elif lang in C_LIKE_LANGS or lang == "gdscript":
        return _parse_c_like_blocks(text, lang)
    elif lang in SCRIPT_LANGS:
        return _parse_script_blocks(text)
    return {}


def _read_file_from_store(path: str, files: dict) -> str | None:
    """Read file content from store by hash."""
    from .store import read_object

    for fpath, hash_spec in files.items():
        if fpath == path:
            obj_hash = hash_spec[7:]
            try:
                return read_object(obj_hash).decode("utf-8")
            except Exception:
                return None
    return None


def _read_file_from_disk(path: str) -> str | None:
    """Read file content from disk."""
    fp = Path(path)
    if not fp.is_file():
        return None
    try:
        return fp.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _format_repo_map_diff(
    path: str,
    lang: str,
    old_blocks: dict[str, tuple[str, str]],
    new_blocks: dict[str, tuple[str, str]],
) -> str:
    """Format repo-map diff with +/- markers."""
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


def _format_repo_map_added(path: str, lang: str, blocks: dict[str, tuple[str, str]]) -> str:
    """Format repo-map for added files."""
    parts = [f"### {path}\n"]
    for _name, (sig, _body) in blocks.items():
        parts.append(f"+ {sig}\n")
    return "".join(parts) if len(parts) > 1 else ""


def gather_files(
    profile: dict[str, Any],
    verbose: bool = False,
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """Gather file contents as formatted strings."""
    tk = tokenizer if tokenizer is not None else count_tokens
    exclude = _get_exclude_patterns(profile)
    sections, _ = _collect_named_sections(profile, exclude, tokenizer=tk, verbose=verbose)
    return [content for _, content, _ in sections]


def gather_command(cmd: str) -> str:
    """Run a command and return its output."""
    return run_command(cmd)


def dry_run(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int] | None = None,
    query: str | None = None,
    mode: str = "full",
) -> dict:
    """Preview collection without writing files.

    Args:
        profile: Profile dict with directories/patterns/files.
        tokenizer: Token counting function. Default: 4 chars ≈ 1 token.
        query: Optional query string to filter files.
        mode: Collection mode — "full", "headers", or "repo-map".

    Returns:
        Dict with name_tmpl, max_tokens, and parts (list of part dicts
        with part_num, sections, total_tokens).
    """
    tk = tokenizer if tokenizer is not None else count_tokens

    exclude = _get_exclude_patterns(profile)
    max_tokens = profile.get("max_tokens", 16000)
    name_tmpl = profile.get("name_template", "chat")

    named_sections, parts, _ = _assemble_content(
        profile,
        exclude,
        tk,
        incremental=False,
        cache=None,
        verbose=False,
        query=query,
        mode=mode,
    )

    # Build per-part section lists
    part_list = []
    for i, content in enumerate(parts, 1):
        part_sections = []
        for name, sec_content, tokens in named_sections:
            if sec_content.strip() in content:
                part_sections.append((name, tokens))
        total_tokens = tk(content)
        part_list.append(
            {
                "part_num": i,
                "sections": part_sections,
                "total_tokens": total_tokens,
            }
        )

    return {"name_tmpl": name_tmpl, "max_tokens": max_tokens, "parts": part_list}


def _get_exclude_patterns(profile: dict[str, Any]) -> list[str]:
    """Build exclusion pattern list from profile and .gitignore."""
    exclude = list(profile.get("exclude_patterns", []))
    if profile.get("use_gitignore", True):
        exclude.extend(load_gitignore_patterns(Path.cwd()))
    return exclude
