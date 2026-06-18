# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""File formatting for markdown output."""

import ast as _ast
import base64
import fnmatch
import json
import os as _os
import re
from pathlib import Path

from .path_utils import validate_path

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
    return _EXT_LANG.get(ext, "")


def _should_skip_binary(path, include_binary, binary_extensions, binary_max_mb):
    ext = path.suffix.lower()
    if ext in _TEXT_EXTENSIONS:
        return False
    try:
        size_mb = path.stat().st_size / (1024 * 1024)
    except OSError:
        return True
    if size_mb > binary_max_mb:
        return True
    if binary_extensions is not None:
        return ext not in binary_extensions
    if not include_binary:
        try:
            with open(path, "rb") as f:
                return b"\x00" in f.read(1024)
        except OSError:
            return True
    return not include_binary


_RE_PY_IMPORT = re.compile(r"^(?:import\s+([\w.,\s]+)|from\s+([\w.]+)\s+import)", re.MULTILINE)
_RE_PY_MULTILINE_IMPORT = re.compile(r"^import\s*\(\s*(.*?)\s*\)", re.MULTILINE | re.DOTALL)

_RE_ES6_IMPORT_FROM = re.compile(
    r"^\s*import\s+[\w{},\s*]+\s*from\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)
_RE_ES6_IMPORT_BARE = re.compile(
    r"^\s*import\s+['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)
_RE_COMMONJS_REQUIRE = re.compile(
    r"^\s*(?:const|let|var)\s+[\w{},\s*]+\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
    re.MULTILINE,
)
_RE_C_INCLUDE = re.compile(r"^\s*#include\s*[<\"]([^>\"]+)[>\"]", re.MULTILINE)
_RE_CSHARP_USING = re.compile(r"^\s*using\s+([\w.]+)\s*;", re.MULTILINE)
_RE_MODULE_USE = re.compile(r"^\s*use\s+([\w\\]+)\s*;", re.MULTILINE)

_C_LIKE_IMPORT_PATTERNS = [
    _RE_ES6_IMPORT_FROM,
    _RE_ES6_IMPORT_BARE,
    _RE_COMMONJS_REQUIRE,
    _RE_C_INCLUDE,
    _RE_CSHARP_USING,
    _RE_MODULE_USE,
]

_RE_C_LIKE_EXPORT = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?(?:function|def|class|interface|enum|struct|trait|impl|"
    r"type\s+\w+\s+\w+|type\s+|public\s+class|public\s+static|public\s+function|fn|func)\s+(\w+)",
    re.MULTILINE,
)

_RE_RUBY_REQUIRE = re.compile(r"^\s*require\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
_RE_SCRIPT_IMPORT_QUOTED = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
_RE_ELIXIR_USE = re.compile(r"^\s*use\s+([\w.]+)", re.MULTILINE)

_SCRIPT_IMPORT_PATTERNS = [
    _RE_RUBY_REQUIRE,
    _RE_SCRIPT_IMPORT_QUOTED,
    _RE_ELIXIR_USE,
]

_RE_RUBY_DEF = re.compile(r"^\s*def\s+(?:self\.)?(\w+[?!]?)", re.MULTILINE)
_RE_ELIXIR_DEFMODULE = re.compile(r"^\s*defmodule\s+([\w.]+)", re.MULTILINE)
_RE_ELIXIR_DEFP = re.compile(r"^\s*defp\s+(\w+)", re.MULTILINE)
_RE_LUA_FUNCTION = re.compile(r"^\s*function\s+(\w+)", re.MULTILINE)

_SCRIPT_EXPORT_PATTERNS = [
    _RE_RUBY_DEF,
    _RE_ELIXIR_DEFMODULE,
    _RE_ELIXIR_DEFP,
    _RE_LUA_FUNCTION,
]


def _generate_header(path: Path, text: str, lang: str) -> str:
    from .language_dispatch import get_header_parser

    parser = get_header_parser(lang)
    if parser is None:
        return ""
    deps, exports = parser(text)
    if not deps and not exports:
        return ""
    lines = [f"### {path}\n"]
    if deps:
        lines.append(f"deps: {', '.join(sorted(set(deps)))}\n")
    if exports:
        lines.append(f"exports: {', '.join(sorted(set(exports)))}\n")
    return "".join(lines)


def _parse_import_stmt(match):
    """Parse a single import statement match, returning list of module names."""
    deps = []
    mod = match.group(1)
    if mod:
        for part in mod.split(","):
            part = part.strip()
            if part:
                deps.append(part)
    mod = match.group(2)
    if mod:
        deps.append(mod)
    return deps


def _parse_multiline_import(match):
    """Parse a multiline import match, returning list of module names."""
    deps = []
    for part in match.group(1).split(","):
        part = part.strip()
        if part:
            deps.append(part)
    return deps


def _parse_python_imports_fallback(text):
    deps = []
    for m in _RE_PY_IMPORT.finditer(text):
        deps.extend(_parse_import_stmt(m))
    for m in _RE_PY_MULTILINE_IMPORT.finditer(text):
        deps.extend(_parse_multiline_import(m))
    return deps


def _parse_python_ast(text):
    deps = []
    exports = []
    tree = _ast.parse(text)
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


def _parse_python(text: str) -> tuple[list[str], list[str]]:
    try:
        return _parse_python_ast(text)
    except SyntaxError:
        return _parse_python_imports_fallback(text), []


def _parse_c_like(text: str) -> tuple[list[str], list[str]]:
    deps = []
    exports = []
    for pattern in _C_LIKE_IMPORT_PATTERNS:
        for m in pattern.finditer(text):
            for group in m.groups():
                if group:
                    deps.append(group)
    for m in _RE_C_LIKE_EXPORT.finditer(text):
        name = m.group(1)
        if name:
            exports.append(name)
    return deps, exports


def _parse_script_deps(text):
    """Extract dependencies from script source."""
    deps = []
    for pattern in _SCRIPT_IMPORT_PATTERNS:
        for m in pattern.finditer(text):
            for group in m.groups():
                if group:
                    deps.append(group)
    return deps


def _parse_script_exports(text):
    """Extract exports from script source."""
    exports = []
    for pattern in _SCRIPT_EXPORT_PATTERNS:
        for m in pattern.finditer(text):
            name = m.group(1)
            if name:
                exports.append(name)
    return exports


def _parse_script(text: str) -> tuple[list[str], list[str]]:
    return _parse_script_deps(text), _parse_script_exports(text)


def _add_line_numbers(text: str) -> str:
    if not text:
        return text
    lines = text.split("\n")
    width = max(5, len(str(len(lines))))
    return "\n".join(f"{i:>{width}}| {line}" for i, line in enumerate(lines, 1))


def _skip_reason_label(path, include_binary, binary_extensions, binary_max_mb):
    try:
        size_mb = path.stat().st_size / (1024 * 1024)
    except OSError:
        return "binary"
    ext = path.suffix.lower()
    if size_mb > binary_max_mb:
        return "binary too large"
    if not include_binary:
        return "binary"
    if binary_extensions is not None and ext not in binary_extensions:
        return "binary not in allowlist"
    return "binary"


def _try_read_text(path):
    try:
        return ("text", path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return ("unicode_error", None)
    except PermissionError:
        return ("permission_error", None)
    except OSError as e:
        return ("os_error", e)


def _handle_unicode_error(path, include_binary, binary_extensions, binary_max_mb, verbose):
    """Handle unicode_error status from file read."""
    if include_binary and _is_binary_allowed(path, binary_extensions, binary_max_mb):
        return ("binary", _format_binary(path, "markdown"))
    if verbose:
        print(f"  Skipped (binary): {path}")
    return ("skip", "")


def _handle_verbose_skip(status, path, detail, verbose):
    """Print skip message for permission/os_error statuses."""
    if verbose:
        if status == "permission_error":
            print(f"  Skipped (permission): {path}")
        elif status == "os_error":
            print(f"  Skipped (error): {path} - {detail}")
    return ("skip", "")


def _handle_read_error(
    status, detail, path, include_binary, binary_extensions, binary_max_mb, verbose
):
    if status == "unicode_error":
        return _handle_unicode_error(
            path, include_binary, binary_extensions, binary_max_mb, verbose
        )
    return _handle_verbose_skip(status, path, detail, verbose)


def _read_text_content(path, include_binary, binary_extensions, binary_max_mb, verbose):
    status, content = _try_read_text(path)
    if status != "text":
        return _handle_read_error(
            status, content, path, include_binary, binary_extensions, binary_max_mb, verbose
        )
    if "\x00" in content:
        if include_binary and _is_binary_allowed(path, binary_extensions, binary_max_mb):
            return ("binary", _format_binary(path, "markdown"))
        if verbose:
            print(f"  Skipped (binary): {path}")
        return ("skip", "")
    return ("text", content)


def _resolve_lang(path, text):
    lang = lang_for_path(path)
    if not lang and text:
        lang = _lang_from_shebang(text.split("\n")[0])
    return lang


def _format_content(path, text, fmt, include_header, line_numbers):
    if line_numbers:
        text = _add_line_numbers(text)
    lang = _resolve_lang(path, text)
    header = _generate_header(path, text, lang) if include_header else ""
    if fmt == "xml":
        return header + _format_xml(path, lang, text)
    elif fmt == "json":
        return header + _format_json(path, lang, text)
    return header + _format_markdown(path, lang, text)


def format_file_section(
    path,
    fmt="markdown",
    include_binary=False,
    binary_extensions=None,
    binary_max_mb=1.0,
    verbose=False,
    include_header=False,
    line_numbers=False,
    root=None,
):
    if root is not None and not validate_path(path, root):
        if verbose:
            print(f"  Skipped (path traversal): {path}")
        return ""
    if _should_skip_binary(path, include_binary, binary_extensions, binary_max_mb):
        if verbose:
            try:
                path.stat()
            except OSError as e:
                print(f"  Skipped (error): {path} - {e}")
                return ""
            reason = _skip_reason_label(path, include_binary, binary_extensions, binary_max_mb)
            print(f"  Skipped ({reason}): {path}")
        return ""
    return _format_valid_file(
        path,
        fmt,
        include_binary,
        binary_extensions,
        binary_max_mb,
        verbose,
        include_header,
        line_numbers,
    )


def _format_valid_file(
    path,
    fmt,
    include_binary,
    binary_extensions,
    binary_max_mb,
    verbose,
    include_header,
    line_numbers,
):
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
    status, content = _read_text_content(
        path, include_binary, binary_extensions, binary_max_mb, verbose
    )
    if status == "skip":
        return ""
    if status == "binary":
        return _format_binary_for_fmt(content, path, fmt)
    return _format_content(path, content, fmt, include_header, line_numbers)


def _format_binary_for_fmt(binary_content, path, fmt):
    if fmt in ("xml", "json"):
        data = Path(path).read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        ext = Path(path).suffix.lstrip(".").lower()
        if fmt == "xml":
            return f'<file path="{path}" encoding="base64" extension="{ext}">\n{b64}\n</file>\n'
        else:
            return (
                json.dumps(
                    {"path": str(path), "encoding": "base64", "content": b64}, ensure_ascii=False
                )
                + "\n"
            )
    return binary_content


def _is_binary_allowed(path, extensions, max_mb):
    if extensions is not None and path.suffix.lower() not in extensions:
        return False
    try:
        return path.stat().st_size / (1024 * 1024) <= max_mb
    except OSError:
        return False


def _format_binary(path, fmt):
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


def _format_markdown(path, lang, text):
    return f"### {path}\n\n```{lang}\n{text}\n```\n"


def _format_xml(path, lang, text):
    lang_attr = f' language="{lang}"' if lang else ""
    return f'<file path="{path}"{lang_attr}>\n<![CDATA[\n{text}\n]]>\n</file>\n'


def _format_json(path, lang, text):
    obj = {"path": str(path), "content": text}
    if lang:
        obj["language"] = lang
    return json.dumps(obj, ensure_ascii=False) + "\n"


def is_excluded(path, exclude_patterns):
    path_str = str(path).replace("\\", "/")
    for pat in exclude_patterns:
        if "/" in pat:
            if _match_directory_pattern(path_str, pat):
                return True
        elif fnmatch.fnmatch(path_str, pat) or fnmatch.fnmatch(path.name, pat):
            return True
    return False


def _match_directory_pattern(path_str, pat):
    parts = path_str.split("/")
    pat_parts = pat.split("/")
    if len(pat_parts) > len(parts):
        return False
    for start in range(len(parts) - len(pat_parts) + 1):
        suffix = "/".join(parts[start:])
        if fnmatch.fnmatch(suffix, pat):
            return True
    return False


def _format_sigs_markdown(filepath, lang, sigs):
    return f"### {filepath}\n\n```{lang if lang else ''}\n{sigs}\n```\n"


def _format_sigs_xml(filepath, lang, sigs):
    lang_attr = f' language="{lang}"' if lang else ""
    return f'<file path="{filepath}"{lang_attr}>\n<![CDATA[\n{sigs}\n]]>\n</file>\n'


def _format_sigs_json(filepath, lang, sigs):
    obj = {"path": str(filepath), "content": sigs}
    if lang:
        obj["language"] = lang
    return json.dumps(obj, ensure_ascii=False) + "\n"


_SIGS_FORMATTERS = {
    "markdown": _format_sigs_markdown,
    "xml": _format_sigs_xml,
    "json": _format_sigs_json,
}


def _apply_repo_map_to_section(filepath, section, raw_text, lang, fmt, include_header, header=""):
    from .splitter import extract_signatures

    if raw_text is None:
        return section
    sigs = extract_signatures(raw_text, lang)
    if not header and include_header:
        header = _generate_header(filepath, raw_text, lang)
    formatter = _SIGS_FORMATTERS.get(fmt, _format_sigs_markdown)
    return header + formatter(filepath, lang, sigs)
