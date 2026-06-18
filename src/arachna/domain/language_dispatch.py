# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Language dispatch — unified parser mapping."""

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
    pass


def _run_with_timeout(func, timeout=_REGEX_TIMEOUT):
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
    text = _RE_STRINGS.sub(" ", text)
    text = _RE_SINGLE_COMMENT.sub(" ", text)
    text = _RE_MULTI_COMMENT.sub(" ", text)
    return text


def _find_matching_brace(text: str, start: int) -> int:
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def _extract_braced_block(text: str, start: int) -> str:
    if start >= len(text) or text[start] != "{":
        return ""
    clean = _strip_strings_and_comments(text[start:])
    depth = 0
    for ch in clean:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : _find_matching_brace(text, start)]
    return text[start:]


_BLOCK_PATTERNS = [
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*def\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?class\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?interface\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?enum\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?struct\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?trait\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?impl\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*type\s+(\w+)\s+\w+[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*type\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*public\s+class\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*public\s+static\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*public\s+function\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*fn\s+(\w+)[^{]*", re.MULTILINE),),
    (re.compile(r"^\s*func\s+(\w+)[^{]*", re.MULTILINE),),
]


def _match_block_pattern(pattern, text, blocks):
    try:
        matches = _run_with_timeout(lambda p=pattern: list(p.finditer(text)))
    except RegexTimeoutError:
        logger.warning("Pattern timed out on input of length %d - skipping", len(text))
        return
    for m in matches:
        sig = m.group(0).strip()
        name = m.group(1)
        if name is None or name in blocks:
            continue
        body_start = m.end()
        if body_start < len(text) and text[body_start] == "{":
            body = _extract_braced_block(text, body_start)
        else:
            body = ""
        blocks[name] = (sig, body)


def _parse_python_blocks(text: str) -> dict | None:
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
            body = "\n".join(lines[node.body[0].lineno - 1 : node.end_lineno]) if node.body else ""
            blocks[name] = (signature, body)
    return blocks


def _parse_c_like_blocks(text: str, lang: str) -> dict:
    blocks = {}
    for (pattern,) in _BLOCK_PATTERNS:
        _match_block_pattern(pattern, text, blocks)
    return blocks


_RE_SCRIPT_DEF = re.compile(
    r"^(\s*def\s+(?:self\.)?(\w+[?!]?).*)",
    re.MULTILINE,
)
_RE_SCRIPT_DEFMODULE = re.compile(
    r"^(\s*defmodule\s+([\w.]+).*)",
    re.MULTILINE,
)
_RE_SCRIPT_DEFP = re.compile(
    r"^(\s*defp\s+(\w+).*)",
    re.MULTILINE,
)
_RE_SCRIPT_FUNCTION = re.compile(
    r"^(\s*function\s+(\w+).*)",
    re.MULTILINE,
)

_SCRIPT_BLOCK_PATTERNS = [
    _RE_SCRIPT_DEF,
    _RE_SCRIPT_DEFMODULE,
    _RE_SCRIPT_DEFP,
    _RE_SCRIPT_FUNCTION,
]


def _parse_script_blocks(text: str) -> dict:
    blocks = {}
    for pattern in _SCRIPT_BLOCK_PATTERNS:
        for m in pattern.finditer(text):
            name = m.group(2)
            sig = m.group(1).strip()
            body = text[m.end() :].strip()
            blocks[name] = (sig, body)
    return blocks


def _build_header_parsers() -> dict:
    parsers = {"python": _header_parse_python, "gdscript": _header_parse_c_like}
    for lang in C_LIKE_LANGS:
        parsers[lang] = _header_parse_c_like
    for lang in SCRIPT_LANGS:
        parsers[lang] = _header_parse_script
    return parsers


def _build_block_parsers() -> dict:
    parsers = {"python": _parse_python_blocks, "gdscript": _parse_c_like_blocks}
    for lang in C_LIKE_LANGS:
        parsers[lang] = _parse_c_like_blocks
    for lang in SCRIPT_LANGS:
        parsers[lang] = _parse_script_blocks
    return parsers


HEADER_PARSERS: dict = _build_header_parsers()
BLOCK_PARSERS: dict = _build_block_parsers()


def get_header_parser(lang: str):
    return HEADER_PARSERS.get(lang)


def get_block_parser(lang: str):
    return BLOCK_PARSERS.get(lang)
