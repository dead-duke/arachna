"""Content gatherer — collects files and runs commands."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .cache import get_changed_files, update_cache
from .compressor import compress
from .formatter import format_file_section, is_excluded
from .gitignore import load_gitignore_patterns
from .runner import run_command
from .splitter import split
from .tokenizer import count_tokens

# Default tokenizer — deprecated, kept for backward compatibility.
# Use tokenizer parameter in function calls instead.
_TOKENIZE: Callable[[str], int] = count_tokens


def get_tokenizer() -> Callable[[str], int]:
    """Return current tokenizer. Deprecated: use explicit tokenizer parameter."""
    return _TOKENIZE


def set_tokenizer(t: Callable[[str], int]):
    """Set global tokenizer. Deprecated: pass tokenizer explicitly to functions."""
    global _TOKENIZE
    _TOKENIZE = t


def _collect_pre_commands(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int] | None = None,
) -> list[tuple[str, str, int]]:
    """Run pre_commands and return (label, output, tokens) tuples."""
    tk = tokenizer if tokenizer is not None else _TOKENIZE
    results = []
    for cmd in profile.get("pre_commands", []):
        output = run_command(cmd)
        if output.strip():
            tokens = tk(output)
            label = cmd if len(cmd) <= 50 else cmd[:47] + "..."
            results.append((f"pre: {label}", output, tokens))
    return results


def _scan_directories(
    profile: dict[str, Any],
    exclude: list[str],
) -> list[Path]:
    """Scan directories for matching files, return sorted Path list."""
    seen = []
    for directory in profile.get("directories", []):
        for pattern in profile.get("patterns", ["*"]):
            for filepath in sorted(Path(directory).rglob(pattern)):
                if not filepath.is_file():
                    continue
                if is_excluded(filepath, exclude):
                    continue
                seen.append(filepath)
    return seen


def _collect_specific_files(
    file_paths: list[str],
    exclude: list[str],
    tokenizer: Callable[[str], int] | None = None,
    fmt: str = "markdown",
    include_binary: bool = False,
    binary_extensions: list[str] | None = None,
    binary_max_mb: float = 1.0,
    verbose: bool = False,
) -> list[tuple[str, str, int]]:
    """Format specific files into (path, content, tokens) tuples."""
    tk = tokenizer if tokenizer is not None else _TOKENIZE
    results = []
    for filepath_str in file_paths:
        filepath = Path(filepath_str)
        if not filepath.exists():
            if verbose:
                print(f"  Not found: {filepath}")
            continue
        if is_excluded(filepath, exclude):
            continue
        section = format_file_section(
            filepath,
            fmt=fmt,
            include_binary=include_binary,
            binary_extensions=binary_extensions,
            binary_max_mb=binary_max_mb,
            verbose=verbose,
        )
        if section:
            tokens = tk(section)
            results.append((str(filepath), section, tokens))
    return results


def _format_scanned_files(
    filepaths: list[Path],
    tokenizer: Callable[[str], int] | None = None,
    fmt: str = "markdown",
    include_binary: bool = False,
    binary_extensions: list[str] | None = None,
    binary_max_mb: float = 1.0,
    verbose: bool = False,
) -> list[tuple[str, str, int]]:
    """Format scanned files into (path, content, tokens) tuples."""
    tk = tokenizer if tokenizer is not None else _TOKENIZE
    results = []
    for filepath in filepaths:
        section = format_file_section(
            filepath,
            fmt=fmt,
            include_binary=include_binary,
            binary_extensions=binary_extensions,
            binary_max_mb=binary_max_mb,
            verbose=verbose,
        )
        if section:
            tokens = tk(section)
            results.append((str(filepath), section, tokens))
    return results


def _collect_named_sections(
    profile: dict[str, Any],
    exclude: list[str],
    incremental: bool = False,
    cache: dict[str, float] | None = None,
    verbose: bool = False,
    tokenizer: Callable[[str], int] | None = None,
) -> tuple[list[tuple[str, str, int]], dict[str, float]]:
    """Collect all named sections from pre_commands, directories, and files.

    Returns (named_sections, updated_cache).
    """
    tk = tokenizer if tokenizer is not None else _TOKENIZE
    fmt = profile.get("section_format", "markdown")
    include_binary = profile.get("include_binary", False)
    binary_extensions = profile.get("binary_extensions")
    binary_max_mb = profile.get("binary_max_mb", 1.0)

    named_sections = []

    # Pre-commands
    named_sections.extend(_collect_pre_commands(profile, tk))

    # Directories
    seen_files = _scan_directories(profile, exclude)

    if incremental and cache is not None:
        changed, new, deleted = get_changed_files(seen_files, cache)
        target_files = changed + new
        if deleted:
            print(f"  Deleted: {len(deleted)} file(s)")
    else:
        target_files = seen_files

    named_sections.extend(
        _format_scanned_files(
            target_files,
            tokenizer=tk,
            fmt=fmt,
            include_binary=include_binary,
            binary_extensions=binary_extensions,
            binary_max_mb=binary_max_mb,
            verbose=verbose,
        )
    )

    # Specific files
    named_sections.extend(
        _collect_specific_files(
            profile.get("files", []),
            exclude,
            tokenizer=tk,
            fmt=fmt,
            include_binary=include_binary,
            binary_extensions=binary_extensions,
            binary_max_mb=binary_max_mb,
            verbose=verbose,
        )
    )

    new_cache = update_cache(target_files, cache or {})

    return named_sections, new_cache


def gather_files(
    profile: dict[str, Any],
    verbose: bool = False,
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """Gather file contents as formatted strings."""
    exclude = _get_exclude_patterns(profile)
    sections, _ = _collect_named_sections(profile, exclude, verbose=verbose, tokenizer=tokenizer)
    return [content for _, content, _ in sections]


def gather_command(cmd: str) -> str:
    """Run a command and return its output."""
    return run_command(cmd)


def dry_run(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int] | None = None,
) -> dict:
    """Preview collection without writing files."""
    tk = tokenizer if tokenizer is not None else _TOKENIZE

    exclude = _get_exclude_patterns(profile)
    max_tokens = profile.get("max_tokens", 16000)
    name_tmpl = profile.get("name_template", "chat")
    split_mode = profile.get("split_mode", "by_file")
    split_marker = profile.get("split_marker", "\n\n")
    command = profile.get("command")
    do_compress = profile.get("compress", False)

    if command:
        content = gather_command(command)
        if do_compress:
            content = compress(content)
        tokens = tk(content)
        named_sections = [("command output", content, tokens)]
    else:
        named_sections, _ = _collect_named_sections(profile, exclude, tokenizer=tk)
        if do_compress:
            named_sections = [
                (name, compress(content), tk(compress(content)))
                for name, content, _ in named_sections
            ]

    raw_content = "\n\n".join(content for _, content, _ in named_sections)
    part_contents = split(raw_content, max_tokens, split_mode, split_marker, tokenizer=tk)

    parts = []
    for i, content in enumerate(part_contents, 1):
        part_sections = []
        for name, sec_content, tokens in named_sections:
            if sec_content.strip() in content:
                part_sections.append((name, tokens))
        total_tokens = tk(content)
        parts.append(
            {
                "part_num": i,
                "sections": part_sections,
                "total_tokens": total_tokens,
            }
        )

    return {"name_tmpl": name_tmpl, "max_tokens": max_tokens, "parts": parts}


def _get_exclude_patterns(profile: dict[str, Any]) -> list[str]:
    """Build exclusion pattern list from profile and .gitignore."""
    exclude = list(profile.get("exclude_patterns", []))
    if profile.get("use_gitignore", True):
        exclude.extend(load_gitignore_patterns(Path.cwd()))
    return exclude
