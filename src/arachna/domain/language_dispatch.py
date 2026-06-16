# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Language dispatch — unified parser mapping for arachna v4.0.1.

Provides HEADER_PARSERS and BLOCK_PARSERS dicts mapping language
names to parser functions. Eliminates duplicated if/elif chains
across formatter, differ_structural, and watcher.

Block parsers (_parse_python_blocks, _parse_c_like_blocks,
_parse_script_blocks) live here to avoid domain->watch dependency.
"""

import ast as _ast
import logging
import re
import threading

from .formatter import C_LIKE_LANGS, SCRIPT_LANGS
from .formatter import _parse_c_like as _header_parse_c_like
from .formatter import _parse_python as _header_parse_python
from .formatter import _parse_script as _header_parse_script

logger = logging.getLogger("arachna.language_dispatch")

_REGEX_TIMEOUT = 0.1


class RegexTimeoutError(Exception):
    """Raised when a regex operation exceeds the timeout."""

    pass


def _run_with_timeout(func, timeout=_REGEX_TIMEOUT):
    """Run function in a daemon thread with timeout. Raises RegexTimeoutError if exceeded."""
    result = [None]
    error = [None]
    done = threading.Event()

    def target():
        try:
            result[0] = func()
        except Exception as e:
            error[0] = e
        finally:
            done.set()

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    if not done.wait(timeout):
        raise RegexTimeoutError(f"Regex operation timed out after {timeout}s")
    if error[0] is not None:
        raise error[0]
    return result[0]


_RE_STRINGS = re.compile(r'"[^"]*"|\'[^\']*\'|`[^`]*`')
_RE_SINGLE_COMMENT = re.compile(r"//[^\n]*")
_RE_MULTI_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_strings_and_comments(text: str) -> str:
    """Strip string literals and comments to avoid false brace matches."""
    text = _RE_STRINGS.sub(" ", text)
    text = _RE_SINGLE_COMMENT.sub(" ", text)
    text = _RE_MULTI_COMMENT.sub(" ", text)
    return text


def _extract_braced_block(text: str, start: int) -> str:
    """Extract a braced block from text starting at position start."""
    if start >= len(text) or text[start] != "{":
        return ""
    clean = _strip_strings_and_comments(text[start:])
    depth = 0
    i = 0
    while i < len(clean):
        if clean[i] == "{":
            depth += 1
        elif clean[i] == "}":
            depth -= 1
            if depth == 0:
                orig_depth = 0
                orig_i = start
                while orig_i < len(text):
                    if text[orig_i] == "{":
                        orig_depth += 1
                    elif text[orig_i] == "}":
                        orig_depth -= 1
                        if orig_depth == 0:
                            return text[start : orig_i + 1]
                    orig_i += 1
                return text[start:]
        i += 1
    return text[start:]


_BLOCK_PATTERNS = [
    (
        re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(?P<name>\w+)[^{]*", re.MULTILINE),
        "name",
    ),
    (re.compile(r"^\s*def\s+(?P<name>\w+)[^{]*", re.MULTILINE), "name"),
    (
        re.compile(r"^\s*(?:export\s+)?(?:async\s+)?class\s+(?P<name>\w+)[^{]*", re.MULTILINE),
        "name",
    ),
    (
        re.compile(r"^\s*(?:export\s+)?(?:async\s+)?interface\s+(?P<name>\w+)[^{]*", re.MULTILINE),
        "name",
    ),
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?enum\s+(?P<name>\w+)[^{]*", re.MULTILINE), "name"),
    (
        re.compile(r"^\s*(?:export\s+)?(?:async\s+)?struct\s+(?P<name>\w+)[^{]*", re.MULTILINE),
        "name",
    ),
    (
        re.compile(r"^\s*(?:export\s+)?(?:async\s+)?trait\s+(?P<name>\w+)[^{]*", re.MULTILINE),
        "name",
    ),
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?impl\s+(?P<name>\w+)[^{]*", re.MULTILINE), "name"),
    (re.compile(r"^\s*type\s+(?P<name>\w+)\s+\w+[^{]*", re.MULTILINE), "name"),
    (re.compile(r"^\s*type\s+(?P<name>\w+)[^{]*", re.MULTILINE), "name"),
    (re.compile(r"^\s*public\s+class\s+(?P<name>\w+)[^{]*", re.MULTILINE), "name"),
    (re.compile(r"^\s*public\s+static\s+(?P<name>\w+)[^{]*", re.MULTILINE), "name"),
    (re.compile(r"^\s*public\s+function\s+(?P<name>\w+)[^{]*", re.MULTILINE), "name"),
    (re.compile(r"^\s*fn\s+(?P<name>\w+)[^{]*", re.MULTILINE), "name"),
    (re.compile(r"^\s*func\s+(?P<name>\w+)[^{]*", re.MULTILINE), "name"),
]


def _parse_python_blocks(text: str) -> dict | None:
    """Parse Python source into named blocks using AST."""
    try:
        tree = _ast.parse(text)
    except SyntaxError:
        return None
    lines = text.split("\n")
    blocks = {}
    for node in _ast.iter_child_nodes(tree):
        if isinstance(node, (_ast.FunctionDef, _ast.ClassDef, _ast.AsyncFunctionDef)):
            name = node.name
            sig_start = node.lineno - 1
            if node.decorator_list:
                sig_start = node.decorator_list[0].lineno - 1
            sig_end = node.body[0].lineno - 1 if node.body else node.end_lineno
            signature = "\n".join(lines[sig_start:sig_end])
            if node.body:
                body_start = node.body[0].lineno - 1
                body = "\n".join(lines[body_start : node.end_lineno])
            else:
                body = ""
            blocks[name] = (signature, body)
    return blocks


def _parse_c_like_blocks(text: str, lang: str) -> dict:
    """Parse C-like source into named blocks using regex patterns."""
    blocks = {}
    for pattern, group_name in _BLOCK_PATTERNS:
        try:
            matches = _run_with_timeout(lambda p=pattern: list(p.finditer(text)))
        except RegexTimeoutError:
            logger.warning("Pattern timed out on input of length %d - skipping", len(text))
            continue
        for m in matches:
            sig = m.group(0).strip()
            name = m.group(group_name)
            if name is None or name in blocks:
                continue
            body_start = m.end()
            if body_start < len(text) and text[body_start] == "{":
                body = _extract_braced_block(text, body_start)
            else:
                body = ""
            blocks[name] = (sig, body)
    return blocks


def _parse_script_blocks(text: str) -> dict:
    """Parse script-language source into named blocks."""
    sig_pattern = re.compile(
        r"^(\s*(?:def\s+(?:self\.)?(\w+[?!]?).*|"
        r"defmodule\s+([\w.]+).*|"
        r"defp\s+(\w+).*|"
        r"function\s+(\w+).*))",
        re.MULTILINE,
    )
    blocks = {}
    for m in sig_pattern.finditer(text):
        name = m.group(2) or m.group(3) or m.group(4) or m.group(5)
        sig = m.group(1).strip()
        body_start = m.end()
        body = text[body_start:].strip()
        blocks[name] = (sig, body)
    return blocks


def _build_header_parsers() -> dict:
    """Build HEADER_PARSERS dict mapping language to header parser function."""
    parsers: dict = {}
    parsers["python"] = _header_parse_python
    for lang in C_LIKE_LANGS:
        parsers[lang] = _header_parse_c_like
    parsers["gdscript"] = _header_parse_c_like
    for lang in SCRIPT_LANGS:
        parsers[lang] = _header_parse_script
    return parsers


def _build_block_parsers() -> dict:
    """Build BLOCK_PARSERS dict mapping language to block parser function."""
    parsers: dict = {}
    parsers["python"] = _parse_python_blocks
    for lang in C_LIKE_LANGS:
        parsers[lang] = _parse_c_like_blocks
    parsers["gdscript"] = _parse_c_like_blocks
    for lang in SCRIPT_LANGS:
        parsers[lang] = _parse_script_blocks
    return parsers


HEADER_PARSERS: dict = _build_header_parsers()
BLOCK_PARSERS: dict = _build_block_parsers()


def get_header_parser(lang: str):
    """Return header parser function for the given language, or None."""
    return HEADER_PARSERS.get(lang)


def get_block_parser(lang: str):
    """Return block parser function for the given language, or None.

    Note: C_LIKE_LANGS parsers accept (text, lang) signature.
    Other parsers accept (text) only.
    """
    return BLOCK_PARSERS.get(lang)
