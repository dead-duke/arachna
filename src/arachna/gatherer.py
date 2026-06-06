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
        for pattern in profile.get("patterns", ["*"]):
            for filepath in sorted(Path(directory).rglob(pattern)):
                if not filepath.is_file():
                    continue
                if filepath.is_symlink():
                    print(f"  Warning: skipping symlink: {filepath}")
                    continue
                if is_excluded(filepath, exclude):
                    continue
                seen.append(filepath)
    return seen


def _collect_specific_files(
    file_paths: list[str],
    exclude: list[str],
    tokenizer: Callable[[str], int],
    fmt: str = "markdown",
    include_binary: bool = False,
    binary_extensions: list[str] | None = None,
    binary_max_mb: float = 1.0,
    verbose: bool = False,
    include_header: bool = False,
    mode: str = "full",
) -> list[tuple[str, str, int]]:
    """Format specific files into (path, content, tokens) tuples.

    For repo-map mode, reads raw text first, applies extract_signatures,
    then formats only the signatures into the output format.
    """
    results = []
    for filepath_str in file_paths:
        filepath = Path(filepath_str)
        if not filepath.exists():
            if verbose:
                print(f"  Not found: {filepath}")
            continue
        if is_excluded(filepath, exclude):
            continue

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
            if mode == "repo-map" and raw_text is not None:
                lang = lang_for_path(filepath)
                sigs = extract_signatures(raw_text, lang)
                header = ""
                if include_header:
                    header = _generate_header(filepath, raw_text, lang)
                if fmt == "xml":
                    section = header + _format_xml_sigs(filepath, lang, sigs)
                elif fmt == "json":
                    section = header + _format_json_sigs(filepath, lang, sigs)
                else:
                    section = header + _format_markdown_sigs(filepath, lang, sigs)

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

    For repo-map mode, reads raw text first, applies extract_signatures,
    then formats only the signatures.
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
            if mode == "repo-map" and raw_text is not None:
                lang = lang_for_path(filepath)
                sigs = extract_signatures(raw_text, lang)
                header = ""
                if include_header:
                    header = _generate_header(filepath, raw_text, lang)
                if fmt == "xml":
                    section = header + _format_xml_sigs(filepath, lang, sigs)
                elif fmt == "json":
                    section = header + _format_json_sigs(filepath, lang, sigs)
                else:
                    section = header + _format_markdown_sigs(filepath, lang, sigs)

            tokens = tokenizer(section)
            results.append((str(filepath), section, tokens))
    return results


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
        if deleted:
            print(f"  Deleted: {len(deleted)} file(s)")
    else:
        target_files = seen_files

    sections = _format_scanned_files(
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

    return _collect_specific_files(
        profile.get("files", []),
        exclude,
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
) -> tuple[list[tuple[str, str, int]], list[str], dict[str, float]]:
    """Assemble content from a command source.

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

    All sections are collected into a single list and packed densely
    via split_sections() for uniform part sizes.

    Returns (named_sections, parts, updated_cache).
    """
    do_compress = profile.get("compress", False)
    max_tokens = profile.get("max_tokens", 16000)

    # Headers auto-enabled when query is used
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
    )

    # Build list of section content strings
    sections = []
    for _name, content, _tokens in named_sections:
        if do_compress and content.strip():
            sections.append(compress(content))
        else:
            sections.append(content)

    if verbose and do_compress:
        raw_tokens = sum(tokens for _name, _content, tokens in named_sections)
        comp_tokens = sum(tokenizer(s) for s in sections)
        if raw_tokens > 0:
            pct = (raw_tokens - comp_tokens) / raw_tokens * 100
            print(f"  Compressed: ~{raw_tokens} -> ~{comp_tokens} tokens (-{pct:.0f}%)")

    # Pack sections densely into token-limited parts
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
        return _assemble_command_content(profile, tokenizer)
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
