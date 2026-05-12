"""File formatting for markdown output."""

import base64
import fnmatch
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

_FILENAME_LANG = {
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    ".env": "bash",
    "procfile": "yaml",
    "vagrantfile": "ruby",
}

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
    if ext in _EXT_LANG:
        return _EXT_LANG[ext]
    return ""


def format_file_section(
    path: Path,
    fmt: str = "markdown",
    include_binary: bool = False,
    binary_extensions: list[str] | None = None,
    binary_max_mb: float = 1.0,
    verbose: bool = False,
) -> str:
    """Read a file and format it as a section."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        if include_binary and _is_binary_allowed(path, binary_extensions, binary_max_mb):
            return _format_binary(path, fmt)
        if verbose:
            print(f"  Skipped (binary): {path}")
        return ""
    except PermissionError:
        if verbose:
            print(f"  Skipped (permission): {path}")
        return ""
    except OSError as e:
        if verbose:
            print(f"  Skipped (error): {path} - {e}")
        return ""

    if "\x00" in text:
        if include_binary and _is_binary_allowed(path, binary_extensions, binary_max_mb):
            return _format_binary(path, fmt)
        if verbose:
            print(f"  Skipped (binary): {path}")
        return ""

    lang = lang_for_path(path)
    if not lang:
        first_line = text.split("\n")[0] if text else ""
        lang = _lang_from_shebang(first_line)

    if fmt == "xml":
        return _format_xml(path, lang, text)
    elif fmt == "json":
        return _format_json(path, lang, text)
    else:
        return _format_markdown(path, lang, text)


def _is_binary_allowed(path: Path, extensions: list[str] | None, max_mb: float) -> bool:
    if not path.exists():
        return False
    if extensions and path.suffix.lower() not in extensions:
        return False
    size_mb = path.stat().st_size / (1024 * 1024)
    return size_mb <= max_mb


def _format_binary(path: Path, fmt: str) -> str:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    ext = path.suffix.lstrip(".").lower()
    if fmt == "xml":
        return f'<file path="{path}" encoding="base64" extension="{ext}">\n{b64}\n</file>\n'
    elif fmt == "json":
        import json as _json

        return (
            _json.dumps(
                {"path": str(path), "encoding": "base64", "content": b64}, ensure_ascii=False
            )
            + "\n"
        )
    else:
        return f"### {path}\n\n```base64\n{b64}\n```\n"


def _format_markdown(path: Path, lang: str, text: str) -> str:
    return f"### {path}\n\n```{lang}\n{text}\n```\n"


def _format_xml(path: Path, lang: str, text: str) -> str:
    lang_attr = f' language="{lang}"' if lang else ""
    return f'<file path="{path}"{lang_attr}>\n<![CDATA[\n{text}\n]]>\n</file>\n'


def _format_json(path: Path, lang: str, text: str) -> str:
    import json as _json

    obj = {"path": str(path), "content": text}
    if lang:
        obj["language"] = lang
    return _json.dumps(obj, ensure_ascii=False) + "\n"


def is_excluded(path: Path, exclude_patterns: list[str]) -> bool:
    path_str = str(path)
    for pat in exclude_patterns:
        if fnmatch.fnmatch(path_str, pat) or fnmatch.fnmatch(path.name, pat):
            return True
    return False
