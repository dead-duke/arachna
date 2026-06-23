"""Pre-commands execution — separated from gatherer_commands to break circular import."""

from collections.abc import Callable
from pathlib import Path

from ...config.profile_config import ProfileConfig
from ..execution.runner import run_pre_commands


def _collect_pre_commands(
    profile: ProfileConfig,
    tokenizer: Callable[[str], int],
    root: Path,
) -> list[tuple[str, str, int]]:
    """Run pre_commands from profile and return labeled output sections.

    Args:
        profile: ProfileConfig with optional 'pre_commands' list.
        tokenizer: Token counting function.
        root: Project root directory.

    Returns:
        List of (label, output, token_count) tuples.
    """
    results = []
    commands = profile.pre_commands
    if not commands:
        return results
    for cmd, output in run_pre_commands(commands, root=root):
        if output.strip():
            tokens = tokenizer(output)
            label = cmd if len(cmd) <= 50 else cmd[:47] + "..."
            results.append((f"pre: {label}", output, tokens))
    return results
