# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Content gatherer facade.

Orchestrates file collection, command execution, and mode dispatch.
Thin facade over gatherer_core, gatherer_query, and gatherer_strategies.
"""

from .compressor import compress as _compress
from .gatherer_core import _get_exclude_patterns, _scan_directories, gather_command, gather_files
from .gatherer_strategies import _get_mode_strategies
from .splitter import split
from .tokenizer import count_tokens

__all__ = [
    "_assemble_content",
    "_scan_directories",
    "dry_run",
    "gather_command",
    "gather_files",
]


def _assemble_command_content(profile, tokenizer, root):
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
        return _assemble_command_content(profile, tokenizer, root)
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
