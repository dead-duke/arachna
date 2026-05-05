"""Gitignore parser — reads .gitignore patterns for auto-exclusion."""

from pathlib import Path


def load_gitignore_patterns(root: Path) -> list[str]:
    """Load all .gitignore patterns from root and its subdirectories.

    Returns list of fnmatch-compatible patterns.
    """
    patterns = []

    for gitignore_path in root.rglob(".gitignore"):
        if not gitignore_path.is_file():
            continue
        try:
            base_dir = gitignore_path.parent
            for line in gitignore_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Make pattern relative to root for fnmatch
                if line.startswith("/"):
                    # Absolute from gitignore location
                    rel = str(base_dir.relative_to(root)) if base_dir != root else ""
                    pattern = f"{rel}/{line[1:]}" if rel else line[1:]
                else:
                    pattern = f"*{line}*" if "/" not in line else f"*{line}*"
                patterns.append(pattern)
        except (OSError, UnicodeDecodeError):
            continue

    return patterns
