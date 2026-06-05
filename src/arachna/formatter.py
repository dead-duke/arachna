"""File formatting for markdown output."""

import ast as _ast
import base64
import fnmatch
import json
import re
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
}

_FILENAME_LANG = {
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    ".env": "bash",
    "procfile": "yaml",
    "vagrantfile": "ruby",
}

# Extensions that are known to be text-based (not binary).
# Generated from _EXT_LANG — single source of truth for language extensions.
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


def _should_skip_binary(
    path: Path,
    include_binary: bool,
    binary_extensions: list[str] | None,
    binary_max_mb: float,
) -> bool:
    """Check if a binary file should be skipped before attempting read_text.

    Text files (with known text extensions) are never skipped.
    Files without extension are treated as potential text files
    and not skipped, unless include_binary is True and they exceed
    the size limit.
    Binary files are skipped unless include_binary=True and they pass
    the size and extension filters.
    """
    if not path.exists():
        return True

    ext = path.suffix.lower()

    # Text files by extension — never skipped
    if ext in _TEXT_EXTENSIONS:
        return False

    # Files without extension — check size, treat as text if within limit
    if not ext:
        if not include_binary:
            return False
        try:
            size_mb = path.stat().st_size / (1024 * 1024)
        except OSError:
            return True
        if size_mb > binary_max_mb:
            return True
        return bool(binary_extensions is not None and "" not in binary_extensions)

    # Binary file handling
    try:
        size_mb = path.stat().st_size / (1024 * 1024)
    except OSError:
        return True

    if size_mb > binary_max_mb:
        return True
    if binary_extensions is not None and ext not in binary_extensions:
        return True
    return not include_binary


# ── Header generation ──────────────────────────────────────────────

# Python: import X, from X import Y
_RE_PY_IMPORT = re.compile(r"^(?:import\s+([\w.]+)|from\s+([\w.]+)\s+import)", re.MULTILINE)

# C-like: import/require/include statements
# Captures: import "pkg" (Go), import ... from '...' (JS/TS),
# require('...') (JS), #include <...> (C/C++), using X; (C#)
_RE_C_LIKE_IMPORT = re.compile(
    r"^\s*(?:import\s+[\w{},\s*]+\s*from\s*['\"]([^'\"]+)['\"]"
    r"|import\s+['\"]([^'\"]+)['\"]"
    r"|(?:const|let|var)\s+[\w{},\s*]+\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
    r"|#include\s*[<\"]([^>\"]+)[>\"]"
    r"|using\s+([\w.]+)\s*;)",
    re.MULTILINE,
)

# C-like exports: function/class/method/type signatures
_RE_C_LIKE_EXPORT = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?(?:function|def|class|interface|enum|struct|trait|impl|"
    r"type\s+|"
    r"public\s+class|public\s+static|public\s+function|"
    r"fn|func)\s+(\w+)",
    re.MULTILINE,
)

# Ruby/Elixir/Lua imports: require, import, use
_RE_SCRIPT_IMPORT = re.compile(
    r"^\s*(?:require\s+['\"]([^'\"]+)['\"]"
    r"|import\s+['\"]([^'\"]+)['\"]"
    r"|use\s+([\w.]+))",
    re.MULTILINE,
)

# Ruby/Elixir/Lua exports: def, defmodule, defp, function
_RE_SCRIPT_EXPORT = re.compile(
    r"^\s*(?:def\s+(?:self\.)?(\w+[?!]?)"
    r"|defmodule\s+([\w.]+)"
    r"|defp\s+(\w+)"
    r"|function\s+(\w+))",
    re.MULTILINE,
)

# Language sets for dispatch
_C_LIKE_LANGS = frozenset(
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
    }
)
_SCRIPT_LANGS = frozenset({"ruby", "elixir", "lua"})


def _generate_header(path: Path, text: str, lang: str) -> str:
    """Generate a context header with dependencies and exports.

    Returns empty string for unknown languages (no crash).
    Format:
        ### path
        deps: dep1, dep2
        exports: func1, func2
    """
    deps: list[str] = []
    exports: list[str] = []

    if lang == "python":
        deps, exports = _parse_python(text)
    elif lang in _C_LIKE_LANGS or lang == "gdscript":
        deps, exports = _parse_c_like(text)
    elif lang in _SCRIPT_LANGS:
        deps, exports = _parse_script(text)
    # Fallback: unknown language → empty header

    if not deps and not exports:
        return ""

    lines = [f"### {path}\n"]
    if deps:
        lines.append(f"deps: {', '.join(sorted(set(deps)))}\n")
    if exports:
        lines.append(f"exports: {', '.join(sorted(set(exports)))}\n")
    return "".join(lines)


def _parse_python(text: str) -> tuple[list[str], list[str]]:
    """Extract imports and top-level function/class names from Python source."""
    deps: list[str] = []
    exports: list[str] = []

    try:
        tree = _ast.parse(text)
    except SyntaxError:
        # Fall back to regex for syntactically invalid Python
        for m in _RE_PY_IMPORT.finditer(text):
            mod = m.group(1) or m.group(2)
            if mod:
                deps.append(mod)
        return deps, exports

    for node in _ast.iter_child_nodes(tree):
        if isinstance(node, _ast.Import):
            for alias in node.names:
                deps.append(alias.name)
        elif isinstance(node, _ast.ImportFrom):
            if node.module:
                deps.append(node.module)
        elif isinstance(node, (_ast.FunctionDef, _ast.ClassDef, _ast.AsyncFunctionDef)):
            exports.append(node.name)

    return deps, exports


def _parse_c_like(text: str) -> tuple[list[str], list[str]]:
    """Extract imports and exports from C-like languages via regex."""
    deps: list[str] = []
    exports: list[str] = []

    for m in _RE_C_LIKE_IMPORT.finditer(text):
        dep = m.group(1) or m.group(2) or m.group(3) or m.group(4) or m.group(5)
        if dep:
            deps.append(dep)

    for m in _RE_C_LIKE_EXPORT.finditer(text):
        name = m.group(1)
        if name:
            exports.append(name)

    return deps, exports


def _parse_script(text: str) -> tuple[list[str], list[str]]:
    """Extract imports and exports from Ruby/Elixir/Lua via regex."""
    deps: list[str] = []
    exports: list[str] = []

    for m in _RE_SCRIPT_IMPORT.finditer(text):
        dep = m.group(1) or m.group(2) or m.group(3)
        if dep:
            deps.append(dep)

    for m in _RE_SCRIPT_EXPORT.finditer(text):
        name = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        if name:
            exports.append(name)

    return deps, exports


# ── End header generation ──────────────────────────────────────────


def format_file_section(
    path: Path,
    fmt: str = "markdown",
    include_binary: bool = False,
    binary_extensions: list[str] | None = None,
    binary_max_mb: float = 1.0,
    verbose: bool = False,
    include_header: bool = False,
) -> str:
    """Read a file and format it as a section."""
    if _should_skip_binary(path, include_binary, binary_extensions, binary_max_mb):
        try:
            path.stat()
        except OSError as e:
            if verbose:
                print(f"  Skipped (error): {path} - {e}")
            return ""
        if verbose:
            size_mb = path.stat().st_size / (1024 * 1024)
            ext = path.suffix.lower()
            if size_mb > binary_max_mb:
                print(f"  Skipped (binary too large): {path}")
            elif not include_binary:
                print(f"  Skipped (binary): {path}")
            elif binary_extensions is not None and ext not in binary_extensions:
                print(f"  Skipped (binary not in allowlist): {path}")
            else:
                print(f"  Skipped (binary): {path}")
        return ""

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

    # Generate header if requested
    header = ""
    if include_header:
        header = _generate_header(path, text, lang)

    if fmt == "xml":
        return header + _format_xml(path, lang, text)
    elif fmt == "json":
        return header + _format_json(path, lang, text)
    else:
        return header + _format_markdown(path, lang, text)


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
        return (
            json.dumps(
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
    obj = {"path": str(path), "content": text}
    if lang:
        obj["language"] = lang
    return json.dumps(obj, ensure_ascii=False) + "\n"


def is_excluded(path: Path, exclude_patterns: list[str]) -> bool:
    path_str = str(path)
    for pat in exclude_patterns:
        if fnmatch.fnmatch(path_str, pat) or fnmatch.fnmatch(path.name, pat):
            return True
    return False
