# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
r"""Gitignore parser — reads .gitignore patterns for auto-exclusion.

Limitations:
- Negation patterns (!important.log) are treated as regular patterns
- Character classes ([abc].txt) are matched literally
- Trailing space escaping (file\ .txt) is not supported
- Double asterisk (**/logs) matches as single-level wildcard
- Only .gitignore files are read; .git/info/exclude and global
  gitignore are not consulted

These limitations are acceptable for arachna's use case: providing
reasonable defaults for project file collection. Users can add
explicit exclude_patterns in .arachna.json for edge cases.
"""

from pathlib import Path

from .config import _COMMON_EXCLUDE_DIRS

_MAX_GITIGNORE_SIZE = 100 * 1024


def load_gitignore_patterns(root: Path) -> list[str]:
    patterns = []
    for gitignore_path in root.rglob(".gitignore"):
        if not gitignore_path.is_file():
            continue
        if gitignore_path.parent.is_symlink():
            continue
        try:
            parts = gitignore_path.parent.relative_to(root).parts
        except ValueError:
            continue
        if any(p.startswith(".") or p in _COMMON_EXCLUDE_DIRS for p in parts):
            continue
        try:
            if gitignore_path.stat().st_size > _MAX_GITIGNORE_SIZE:
                continue
        except OSError:
            continue
        try:
            text = gitignore_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "\x00" in text:
            continue
        base_dir = gitignore_path.parent
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("/"):
                try:
                    rel = str(base_dir.relative_to(root)) if base_dir != root else ""
                except ValueError:
                    continue
                pattern = f"{rel}/{line[1:]}" if rel else line[1:]
            else:
                try:
                    rel = str(base_dir.relative_to(root)) if base_dir != root else ""
                except ValueError:
                    continue
                pattern = f"{rel}/{line}" if rel else line
            patterns.append(pattern)
    return patterns
