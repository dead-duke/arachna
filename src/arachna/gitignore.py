"""Gitignore parser — reads .gitignore patterns for auto-exclusion."""

from pathlib import Path

# Directories always excluded from gitignore loading
EXCLUDED_DIRS = frozenset(
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

# Max .gitignore file size (100 KB)
_MAX_GITIGNORE_SIZE = 100 * 1024


def load_gitignore_patterns(root: Path) -> list[str]:
    """Load all .gitignore patterns from root and its subdirectories."""
    patterns = []

    for gitignore_path in root.rglob(".gitignore"):
        if not gitignore_path.is_file():
            continue

        # Skip gitignore files in excluded directories
        parts = gitignore_path.parent.relative_to(root).parts
        if any(p.startswith(".") or p in EXCLUDED_DIRS for p in parts):
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
                rel = str(base_dir.relative_to(root)) if base_dir != root else ""
                pattern = f"{rel}/{line[1:]}" if rel else line[1:]
            else:
                # Pattern applies from base_dir downwards
                rel = str(base_dir.relative_to(root)) if base_dir != root else ""
                pattern = f"{rel}/{line}" if rel else line

            patterns.append(pattern)

    return patterns
