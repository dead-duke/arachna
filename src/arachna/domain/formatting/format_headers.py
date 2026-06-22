"""File header generation — deps and exports extraction for all languages."""

import ast as _ast
import re
from pathlib import Path

_RE_PY_IMPORT_SIMPLE = re.compile(r"^import\s+([\w., ]+)", re.MULTILINE)
_RE_PY_IMPORT_FROM = re.compile(r"^from\s+([\w.]+)\s+import", re.MULTILINE)
_RE_PY_MULTILINE_IMPORT = re.compile(r"^import\s*\(\s*([^)]*)\s*\)", re.MULTILINE)

_RE_ES6_IMPORT_FROM_DESTRUCTURE = re.compile(
    r"^\s*import\s+(?:type\s+)?\{[^}]+\}\s*from\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)
_RE_ES6_IMPORT_FROM_SIMPLE = re.compile(
    r"^\s*import\s+(?:type\s+)?\w+\s+from\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)
_RE_ES6_IMPORT_BARE = re.compile(
    r"^\s*import\s+['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)
_RE_COMMONJS_REQUIRE_DESTRUCTURE = re.compile(
    r"^\s*(?:const|let|var)\s*\{[^}]+\}\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
    re.MULTILINE,
)
_RE_COMMONJS_REQUIRE_SIMPLE = re.compile(
    r"^\s*(?:const|let|var)\s+\w+\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
    re.MULTILINE,
)
_RE_C_INCLUDE = re.compile(r"^\s*#include\s*[<\"]([^>\"]+)[>\"]", re.MULTILINE)
_RE_CSHARP_USING = re.compile(r"^\s*using\s+([\w.]+)\s*;", re.MULTILINE)
_RE_MODULE_USE = re.compile(r"^\s*use\s+([\w\\]+)\s*;", re.MULTILINE)

_C_LIKE_IMPORT_PATTERNS = [
    _RE_ES6_IMPORT_FROM_DESTRUCTURE,
    _RE_ES6_IMPORT_FROM_SIMPLE,
    _RE_ES6_IMPORT_BARE,
    _RE_COMMONJS_REQUIRE_DESTRUCTURE,
    _RE_COMMONJS_REQUIRE_SIMPLE,
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


def _parse_import_stmt(match):
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
    deps = []
    for part in match.group(1).split(","):
        part = part.strip()
        if part:
            deps.append(part)
    return deps


def _parse_python_imports_fallback(text):
    deps = []
    for m in _RE_PY_IMPORT_SIMPLE.finditer(text):
        for part in m.group(1).split(","):
            part = part.strip()
            if part:
                deps.append(part)
    for m in _RE_PY_IMPORT_FROM.finditer(text):
        mod = m.group(1)
        if mod:
            deps.append(mod)
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
    deps = []
    for pattern in _SCRIPT_IMPORT_PATTERNS:
        for m in pattern.finditer(text):
            for group in m.groups():
                if group:
                    deps.append(group)
    return deps


def _parse_script_exports(text):
    exports = []
    for pattern in _SCRIPT_EXPORT_PATTERNS:
        for m in pattern.finditer(text):
            name = m.group(1)
            if name:
                exports.append(name)
    return exports


def _parse_script(text: str) -> tuple[list[str], list[str]]:
    return _parse_script_deps(text), _parse_script_exports(text)


def _generate_header(path: Path, text: str, lang: str) -> str:
    from ..tokenization.language_dispatch import get_header_parser

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
