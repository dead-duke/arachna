# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Language detection — extensions, filenames, shebang parsing."""

from pathlib import Path

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
    "in": "ini",
    "txt": "text",
    "js": "javascript",
    "jsx": "jsx",
    "ts": "typescript",
    "tsx": "tsx",
    "html": "html",
    "css": "css",
    "sql": "sql",
    "rs": "rust",
    "go": "go",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "h": "c",
    "hpp": "cpp",
    "gd": "gdscript",
    "cs": "csharp",
    "swift": "swift",
    "kt": "kotlin",
    "rb": "ruby",
    "php": "php",
    "tf": "hcl",
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    "gitignore": "gitignore",
    "zig": "zig",
    "lua": "lua",
    "ex": "elixir",
    "exs": "elixir",
    "hs": "haskell",
    "lhs": "haskell",
    "gleam": "gleam",
    "cmake": "cmake",
    "gradle": "groovy",
    "lock": "text",
    "conf": "ini",
    "1": "nroff",
}

_FILENAME_LANG = {
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    ".env": "bash",
    "procfile": "yaml",
    "vagrantfile": "ruby",
}

_TEXT_EXTENSIONS = frozenset(f".{ext}" for ext in _EXT_LANG)

_SHEBANG_MAP = {
    "python": "python",
    "python3": "python",
    "python2": "python",
    "bash": "bash",
    "sh": "bash",
    "zsh": "bash",
    "node": "javascript",
    "ruby": "ruby",
    "perl": "perl",
}

C_LIKE_LANGS = frozenset(
    {
        "javascript",
        "typescript",
        "rust",
        "go",
        "java",
        "cpp",
        "c",
        "csharp",
        "swift",
        "kotlin",
        "php",
        "zig",
        "gleam",
    }
)
SCRIPT_LANGS = frozenset({"ruby", "elixir", "lua"})


def _lang_from_shebang(first_line: str) -> str:
    if not first_line.startswith("#!"):
        return ""
    parts = first_line[2:].strip().split()
    if not parts:
        return ""
    if "env" in parts[0]:
        if len(parts) > 1:
            binary = parts[1]
        else:
            return ""
    else:
        binary = parts[0].split("/")[-1]
    return _SHEBANG_MAP.get(binary, "")


def lang_for_path(path: Path) -> str:
    name = path.name.lower()
    if name in _FILENAME_LANG:
        return _FILENAME_LANG[name]
    ext = path.suffix.lstrip(".").lower()
    return _EXT_LANG.get(ext, "")
