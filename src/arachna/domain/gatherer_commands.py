# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Command execution for arachna v4.2.0.

Extracted from gatherer_core.py during v4.2.0 decomposition.
Handles pre_commands execution and command output gathering.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .runner import run_command, run_pre_commands
from .tokenizer import count_tokens


def _collect_pre_commands(
    profile: dict[str, Any],
    tokenizer: Callable[[str], int],
    root: Path,
) -> list[tuple[str, str, int]]:
    """Run pre_commands from profile and return labeled output sections.

    Args:
        profile: Profile dict with optional 'pre_commands' list.
        tokenizer: Token counting function.
        root: Project root directory.

    Returns:
        List of (label, output, token_count) tuples.
    """
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


def gather_files(
    profile: dict[str, Any],
    root: Path,
    verbose: bool = False,
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """Gather files by profile, return list of formatted content strings.

    Args:
        profile: Profile dict.
        root: Project root directory.
        verbose: Whether to print progress.
        tokenizer: Token counting function (default: count_tokens).

    Returns:
        List of formatted file content strings.
    """
    from .gatherer_files import _collect_named_sections

    tk = tokenizer if tokenizer is not None else count_tokens
    exclude = _get_exclude_patterns_for_gather(profile, root=root)
    sections, _ = _collect_named_sections(
        profile, exclude, tokenizer=tk, root=root, verbose=verbose
    )
    return [content for _, content, _ in sections]


def _get_exclude_patterns_for_gather(profile: dict[str, Any], root: Path) -> list[str]:
    """Get exclude patterns for gather_files (thin wrapper)."""
    from .gatherer_files import _get_exclude_patterns

    return _get_exclude_patterns(profile, root)


def gather_command(cmd: str, root: Path) -> str:
    """Execute a shell command and return its output.

    Args:
        cmd: Shell command to execute.
        root: Project root directory.

    Returns:
        Command stdout as string.
    """
    return run_command(cmd, root=root, allow_file_args=True)
