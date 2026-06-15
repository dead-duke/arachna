# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""File formatting for markdown output."""

import ast as _ast
import base64
import fnmatch
import json
import os as _os
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

# Language sets for dispatch - single source of truth.
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

_ARACHNA_MAX_FILE_SIZE = int(_os.environ.get("ARACHNA_MAX_FILE_SIZE", 100 * 1024 * 1024))


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
    """Check if a file should be skipped as binary - decision table."""
    ext = path.suffix.lower()
    if ext in _TEXT_EXTENSIONS:
        return False

    try:
        size_mb = path.stat().st_size / (1024 * 1024)
    except OSError:
        return True

    if size_mb > binary_max_mb:
        return True

    if not ext:
        if not include_binary:
            try:
                with open(path, "rb") as f:
                    chunk = f.read(1024)
                return b"\x00" in chunk
            except OSError:
                return True
        return bool(binary_extensions is not None and "" not in binary_extensions)

    if binary_extensions is not None and ext not in binary_extensions:
        return True
    return not include_binary


_RE_PY_IMPORT = re.compile(r"^(?:import\s+([\w.,\s]+)|from\s+([\w.]+)\s+import)", re.MULTILINE)
_RE_PY_MULTILINE_IMPORT = re.compile(r"^import\s*\(\s*(.*?)\s*\)", re.MULTILINE | re.DOTALL)

_RE_C_LIKE_IMPORT = re.compile(
    r"^\s*(?:import\s+[\w{},\s*]+\s*from\s*['\"]([^'\"]+)['\"]"
    r"|import\s+['\"]([^'\"]+)['\"]"
    r"|(?:const|let|var)\s+[\w{},\s*]+\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
    r"|#include\s*[<\"]([^>\"]+)[>\"]"
    r"|using\s+([\w.]+)\s*;"
    r"|use\s+([\w\\]+)\s*;)",
    re.MULTILINE,
)

_RE_C_LIKE_EXPORT = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?(?:function|def|class|interface|enum|struct|trait|impl|"
    r"type\s+|"
    r"public\s+class|public\s+static|public\s+function|"
    r"fn|func)\s+(\w+)",
    re.MULTILINE,
)

_RE_SCRIPT_IMPORT = re.compile(
    r"^\s*(?:require\s+['\"]([^'\"]+)['\"]"
    r"|import\s+['\"]([^'\"]+)['\"]"
    r"|use\s+([\w.]+))",
    re.MULTILINE,
)

_RE_SCRIPT_EXPORT = re.compile(
    r"^\s*(?:def\s+(?:self\.)?(\w+[?!]?)"
    r"|defmodule\s+([\w.]+)"
    r"|defp\s+(\w+)"
    r"|function\s+(\w+))",
    re.MULTILINE,
)


def _generate_header(path: Path, text: str, lang: str) -> str:
    deps: list[str] = []
    exports: list[str] = []

    if lang == "python":
        deps, exports = _parse_python(text)
    elif lang in C_LIKE_LANGS or lang == "gdscript":
        deps, exports = _parse_c_like(text)
    elif lang in SCRIPT_LANGS:
        deps, exports = _parse_script(text)

    if not deps and not exports:
        return ""

    lines = [f"### {path}\n"]
    if deps:
        lines.append(f"deps: {', '.join(sorted(set(deps)))}\n")
    if exports:
        lines.append(f"exports: {', '.join(sorted(set(exports)))}\n")
    return "".join(lines)


def _parse_python(text: str) -> tuple[list[str], list[str]]:
    deps: list[str] = []
    exports: list[str] = []

    try:
        tree = _ast.parse(text)
    except SyntaxError:
        for m in _RE_PY_IMPORT.finditer(text):
            mod = m.group(1)
            if mod:
                for part in mod.split(","):
                    part = part.strip()
                    if part:
                        deps.append(part)
            mod = m.group(2)
            if mod:
                deps.append(mod)
        for m in _RE_PY_MULTILINE_IMPORT.finditer(text):
            inner = m.group(1)
            for part in inner.split(","):
                part = part.strip()
                if part:
                    deps.append(part)
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
    deps: list[str] = []
    exports: list[str] = []

    for m in _RE_C_LIKE_IMPORT.finditer(text):
        dep = m.group(1) or m.group(2) or m.group(3) or m.group(4) or m.group(5) or m.group(6)
        if dep:
            deps.append(dep)

    for m in _RE_C_LIKE_EXPORT.finditer(text):
        name = m.group(1)
        if name:
            exports.append(name)

    return deps, exports


def _parse_script(text: str) -> tuple[list[str], list[str]]:
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


def format_file_section(
    path: Path,
    fmt: str = "markdown",
    include_binary: bool = False,
    binary_extensions: list[str] | None = None,
    binary_max_mb: float = 1.0,
    verbose: bool = False,
    include_header: bool = False,
) -> str:
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
        st_size = path.stat().st_size
    except OSError as e:
        if verbose:
            print(f"  Skipped (error): {path} - {e}")
        return ""
    if st_size > _ARACHNA_MAX_FILE_SIZE:
        if verbose:
            size_mb = st_size / (1024 * 1024)
            limit_mb = _ARACHNA_MAX_FILE_SIZE / (1024 * 1024)
            print(f"  Skipped (file too large: {size_mb:.1f}MB > {limit_mb:.0f}MB): {path}")
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
    """Check if a binary file is allowed based on extension and size."""
    if extensions is not None and path.suffix.lower() not in extensions:
        return False
    try:
        size_mb = path.stat().st_size / (1024 * 1024)
    except OSError:
        return False
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
