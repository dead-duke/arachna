"""Gitignore parser — reads .gitignore patterns for auto-exclusion."""

from pathlib import Path

from .config import _COMMON_EXCLUDE_DIRS

# 100 KB — верхняя граница разумного .gitignore:
# даже в монорепо с сотнями правил файл редко превышает 10-20 KB.
_MAX_GITIGNORE_SIZE = 100 * 1024


def load_gitignore_patterns(root: Path) -> list[str]:
    """Load all .gitignore patterns from root and its subdirectories."""
    patterns = []

    for gitignore_path in root.rglob(".gitignore"):
        if not gitignore_path.is_file():
            continue

        # Skip gitignore files in symlinked directories
        if gitignore_path.parent.is_symlink():
            continue

        # Skip gitignore files in excluded directories
        try:
            parts = gitignore_path.parent.relative_to(root).parts
        except ValueError:
            # gitignore is outside root (e.g., symlinks) — skip
            continue

        if any(p.startswith(".") or p in _COMMON_EXCLUDE_DIRS for p in parts):
            continue

        # Check file size before reading
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
                    continue  # symlink outside root, skip
                pattern = f"{rel}/{line[1:]}" if rel else line[1:]
            else:
                try:
                    rel = str(base_dir.relative_to(root)) if base_dir != root else ""
                except ValueError:
                    continue  # symlink outside root, skip
                pattern = f"{rel}/{line}" if rel else line

            patterns.append(pattern)

    return patterns
