"""File formatting for markdown output."""

import fnmatch
from pathlib import Path

# Language mapping by file extension
_EXT_LANG = {
    "py": "python",
    "json": "json",
    "toml": "toml",
    "yaml": "yaml",
    "yml": "yaml",
    "md": "markdown",
    "sh": "bash",
    "cfg": "ini",
    "ini": "ini",
    "txt": "text",
    "js": "javascript",
    "ts": "typescript",
    "html": "html",
    "css": "css",
    "sql": "sql",
    "rs": "rust",
    "go": "go",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "h": "c",
    "makefile": "makefile",
    "gitignore": "gitignore",
}

# Language mapping by filename (no extension)
_FILENAME_LANG = {
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    ".env": "bash",
    "procfile": "yaml",
    "vagrantfile": "ruby",
}


def lang_for_path(path: Path) -> str:
    """Detect markdown code block language for a file path."""
    name = path.name.lower()
    if name in _FILENAME_LANG:
        return _FILENAME_LANG[name]
    ext = path.suffix.lstrip(".").lower()
    return _EXT_LANG.get(ext, "")


def format_file_section(path: Path) -> str:
    """Read a file and format it as a markdown section.

    Returns empty string if file cannot be read.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError, OSError):
        return ""

    lang = lang_for_path(path)
    return f"### {path}\n\n```{lang}\n{text}\n```\n"


def is_excluded(path: Path, exclude_patterns: list[str]) -> bool:
    """Check if file matches any exclude pattern."""
    path_str = str(path)
    for pat in exclude_patterns:
        if fnmatch.fnmatch(path_str, pat) or fnmatch.fnmatch(path.name, pat):
            return True
    return False
