# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Path validation utilities for arachna."""

from pathlib import Path


def validate_path(path: Path, root: Path) -> bool:
    """Check that path is within root directory.

    Resolves both paths to absolute paths and verifies that path
    is a descendant of root. Used to prevent path traversal attacks
    in file I/O operations (SonarCloud S2083).

    Args:
        path: The path to validate.
        root: The root directory that path must be within.

    Returns:
        True if path is within root, False otherwise.
    """
    try:
        resolved_path = path.resolve()
        resolved_root = root.resolve()
        resolved_path.relative_to(resolved_root)
        return True
    except (ValueError, OSError):
        return False
