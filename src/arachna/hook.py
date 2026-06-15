# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Git hook installer for arachna."""

import stat
from pathlib import Path

from .config import load_config

_HOOK_SCRIPT_TEMPLATE = "#!/bin/sh\n{command}\n"


def install_hook(
    command: str | None = None,
    force: bool = False,
    root: Path | None = None,
) -> tuple[bool, str]:
    """Install post-commit hook to run arachna after each commit.

    Args:
        command: Shell command to run in the hook. If None, reads from
                 .arachna.json hook.post-commit, falls back to "arachna collect --all".
        force: Overwrite existing hook without confirmation prompt.
        root: Project root directory (default: cwd).

    Returns:
        (success, message) tuple.
    """
    if root is None:
        root = Path.cwd()

    # Check this is a git repository
    git_dir = root / ".git"
    if not git_dir.is_dir():
        return False, "Not a git repository (.git directory not found)"

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "post-commit"

    # Resolve command
    if command is None:
        try:
            config = load_config(root=root)
            hook_config = config.get("hook", {})
            command = hook_config.get("post-commit", "arachna collect --all")
        except Exception:
            command = "arachna collect --all"

    # Check if hook already exists
    if hook_path.exists():
        if not force:
            return False, (
                f"post-commit hook already exists at {hook_path}. Use --force to overwrite."
            )
        hook_path.unlink()

    # Write hook script
    script = _HOOK_SCRIPT_TEMPLATE.format(command=command)
    hook_path.write_text(script)

    # Make executable — owner and group only, not world-executable
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

    return True, f"post-commit hook installed: {hook_path} (command: {command})"
