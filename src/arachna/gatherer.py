"""Content gatherer — collects files and runs commands."""

from pathlib import Path
from typing import Any

from .cache import get_changed_files, update_cache
from .compressor import compress
from .formatter import format_file_section, is_excluded
from .gitignore import load_gitignore_patterns
from .runner import run_command
from .splitter import split
from .tokenizer import count_tokens


def _get_exclude_patterns(profile: dict[str, Any]) -> list[str]:
    exclude = list(profile.get("exclude_patterns", []))
    if profile.get("use_gitignore", True):
        exclude.extend(load_gitignore_patterns(Path.cwd()))
    return exclude


def _collect_named_sections(
    profile: dict[str, Any],
    exclude: list[str],
    incremental: bool = False,
    cache: dict[str, float] | None = None,
    verbose: bool = False,
) -> tuple[list[tuple[str, str, int]], dict[str, float]]:
    named_sections = []
    seen_files = []
    fmt = profile.get("section_format", "markdown")
    include_binary = profile.get("include_binary", False)
    binary_extensions = profile.get("binary_extensions")
    binary_max_mb = profile.get("binary_max_mb", 1.0)

    for cmd in profile.get("pre_commands", []):
        output = run_command(cmd)
        if output.strip():
            tokens = count_tokens(output)
            label = cmd if len(cmd) <= 50 else cmd[:47] + "..."
            named_sections.append((f"pre: {label}", output, tokens))

    for directory in profile.get("directories", []):
        for pattern in profile.get("patterns", ["*"]):
            for filepath in sorted(Path(directory).rglob(pattern)):
                if not filepath.is_file():
                    continue
                if is_excluded(filepath, exclude):
                    continue
                seen_files.append(filepath)

    if incremental and cache is not None:
        changed, new, deleted = get_changed_files(seen_files, cache)
        target_files = changed + new
        if deleted:
            print(f"  Deleted: {len(deleted)} file(s)")
    else:
        target_files = seen_files

    for filepath in target_files:
        section = format_file_section(
            filepath,
            fmt=fmt,
            include_binary=include_binary,
            binary_extensions=binary_extensions,
            binary_max_mb=binary_max_mb,
            verbose=verbose,
        )
        if section:
            tokens = count_tokens(section)
            named_sections.append((str(filepath), section, tokens))

    for filepath_str in profile.get("files", []):
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
            tokens = count_tokens(section)
            named_sections.append((str(filepath), section, tokens))

    new_cache = update_cache(target_files, cache or {})

    return named_sections, new_cache


def gather_files(profile: dict[str, Any], verbose: bool = False) -> list[str]:
    exclude = _get_exclude_patterns(profile)
    sections, _ = _collect_named_sections(profile, exclude, verbose=verbose)
    return [content for _, content, _ in sections]


def gather_command(cmd: str) -> str:
    return run_command(cmd)


def dry_run(profile: dict[str, Any]) -> dict:
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
        tokens = count_tokens(content)
        named_sections = [("command output", content, tokens)]
    else:
        named_sections, _ = _collect_named_sections(profile, exclude)
        if do_compress:
            named_sections = [
                (name, compress(content), count_tokens(compress(content)))
                for name, content, _ in named_sections
            ]

    raw_content = "\n\n".join(content for _, content, _ in named_sections)
    part_contents = split(raw_content, max_tokens, split_mode, split_marker)

    parts = []
    for i, content in enumerate(part_contents, 1):
        part_sections = []
        for name, sec_content, tokens in named_sections:
            if sec_content.strip() in content:
                part_sections.append((name, tokens))
        total_tokens = count_tokens(content)
        parts.append(
            {
                "part_num": i,
                "sections": part_sections,
                "total_tokens": total_tokens,
            }
        )

    return {"name_tmpl": name_tmpl, "max_tokens": max_tokens, "parts": parts}
