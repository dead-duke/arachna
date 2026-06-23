"""Content gatherer facade.

Orchestrates file collection, command execution, and mode dispatch.
Thin facade over gatherer_files, gatherer_commands, and gatherer_strategies.
"""

import logging

from ...config import CollectionMode
from ..compressor import compress as _compress
from ..execution.splitter import split
from ..interfaces import Tokenizer
from ..tokenization.tokenizer import count_tokens
from .gatherer_commands import gather_command, gather_files
from .gatherer_files import _get_exclude_patterns, _print_compress_stats, _scan_directories
from .gatherer_strategies import get_mode_strategies

logger = logging.getLogger("arachna.gatherer")

__all__ = [
    "_assemble_content",
    "_scan_directories",
    "dry_run",
    "gather_command",
    "gather_files",
]


def _assemble_command_content(profile, tokenizer, root):
    command = profile.command
    do_compress = profile.compress
    split_mode = profile.split_mode
    split_marker = profile.split_marker
    max_tokens = profile.max_tokens
    raw_content = gather_command(command, root=root)
    raw_tokens = tokenizer(raw_content)
    if do_compress and raw_content.strip():
        raw_content = _compress(raw_content)
    comp_tokens = tokenizer(raw_content)
    if do_compress and raw_tokens > 0:
        _print_compress_stats(raw_tokens, comp_tokens)
    named_sections = [("command output", raw_content, comp_tokens)]
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
    mode: CollectionMode = "full",
):
    strategies = get_mode_strategies()
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
    mode: CollectionMode = "full",
):
    if profile.command:
        if profile.directories or profile.files:
            logger.warning(
                "profile has both 'command' and 'directories'/'files'. Using 'command', ignoring directories and files."
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


def dry_run(
    profile, root, tokenizer: Tokenizer | None = None, query=None, mode: CollectionMode = "full"
):
    tk = tokenizer if tokenizer is not None else count_tokens
    exclude = _get_exclude_patterns(profile, root=root)
    max_tokens = profile.max_tokens
    name_tmpl = profile.name_template
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
