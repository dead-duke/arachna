"""Command execution.

Handles pre_commands execution and command output gathering.
"""

from collections.abc import Callable
from pathlib import Path

from ...config.profile_config import ProfileConfig
from ..execution.runner import run_command
from ..tokenization.tokenizer import count_tokens
from .gatherer_files import _collect_named_sections, _get_exclude_patterns
from .gatherer_pre_commands import _collect_pre_commands

__all__ = ["_collect_pre_commands", "gather_command", "gather_files"]


def gather_files(
    profile: ProfileConfig,
    root: Path,
    verbose: bool = False,
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """Gather files by profile, return list of formatted content strings."""
    tk = tokenizer if tokenizer is not None else count_tokens
    exclude = _get_exclude_patterns_for_gather(profile, root=root)
    sections, _ = _collect_named_sections(
        profile, exclude, tokenizer=tk, root=root, verbose=verbose
    )
    return [content for _, content, _ in sections]


def _get_exclude_patterns_for_gather(profile: ProfileConfig, root: Path) -> list[str]:
    """Get exclude patterns for gather_files (thin wrapper)."""
    return _get_exclude_patterns(profile, root)


def gather_command(cmd: str, root: Path) -> str:
    """Execute a shell command and return its output."""
    return run_command(cmd, root=root, allow_file_args=True)
