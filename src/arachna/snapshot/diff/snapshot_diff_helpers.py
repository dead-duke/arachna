# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Shared helpers for snapshot diff — path normalization, no dependencies."""

import re
from pathlib import Path


def _rel_path(absolute_path: Path, root: Path) -> str:
    """Convert absolute path to relative path from root, normalizing separators."""
    try:
        return _normalize_path(str(absolute_path.resolve().relative_to(root)))
    except ValueError:
        return _normalize_path(str(absolute_path))


def _normalize_path(path: str) -> str:
    """Normalize path separators to forward slashes and collapse duplicates."""
    path = path.replace("\\", "/")
    path = re.sub(r"/+", "/", path)
    return path
