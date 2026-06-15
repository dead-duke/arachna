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
    if root is None:
        root = Path.cwd()

    git_dir = root / ".git"
    if not git_dir.is_dir():
        return False, "Not a git repository (.git directory not found)"

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "post-commit"

    if command is None:
        try:
            config = load_config(root=root)
            hook_config = config.get("hook", {})
            command = hook_config.get("post-commit", "arachna collect --all")
        except Exception:
            command = "arachna collect --all"

    if hook_path.exists():
        if not force:
            return False, (
                f"post-commit hook already exists at {hook_path}. Use --force to overwrite."
            )
        hook_path.unlink()

    script = _HOOK_SCRIPT_TEMPLATE.format(command=command)
    hook_path.write_text(script)

    hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

    return True, f"post-commit hook installed: {hook_path} (command: {command})"
