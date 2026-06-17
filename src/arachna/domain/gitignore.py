# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
r"""Gitignore parser - reads .gitignore patterns for auto-exclusion.

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

_COMMON_EXCLUDE_DIRS = frozenset(
    {
        ".git",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "venv",
        "node_modules",
    }
)

_MAX_GITIGNORE_SIZE = 100 * 1024


def _should_skip_gitignore(gitignore_path: Path, root: Path) -> bool:
    if not gitignore_path.is_file():
        return True
    if gitignore_path.parent.is_symlink():
        return True
    try:
        parts = gitignore_path.parent.relative_to(root).parts
    except ValueError:
        return True
    if any(p.startswith(".") or p in _COMMON_EXCLUDE_DIRS for p in parts):
        return True
    try:
        if gitignore_path.stat().st_size > _MAX_GITIGNORE_SIZE:
            return True
    except OSError:
        return True
    try:
        text = gitignore_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return True
    return "\x00" in text


def _parse_gitignore_lines(text: str, base_dir: Path, root: Path) -> list[str]:
    patterns = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rel = str(base_dir.relative_to(root)) if base_dir != root else ""
        except ValueError:
            continue
        if line.startswith("/"):
            pattern = f"{rel}/{line[1:]}" if rel else line[1:]
        else:
            pattern = f"{rel}/{line}" if rel else line
        patterns.append(pattern)
    return patterns


def load_gitignore_patterns(root: Path) -> list[str]:
    patterns = []
    for gitignore_path in root.rglob(".gitignore"):
        if _should_skip_gitignore(gitignore_path, root):
            continue
        text = gitignore_path.read_text(encoding="utf-8")
        base_dir = gitignore_path.parent
        patterns.extend(_parse_gitignore_lines(text, base_dir, root))
    return patterns
