"""Split content into token-limited parts."""

import logging
import re
from collections.abc import Callable

from .tokenizer import count_tokens

logger = logging.getLogger("arachna.splitter")


def split(
    raw_content: str,
    max_tokens: int,
    mode: str = "by_file",
    marker: str = "\n\n",
    separator: str = "\n\n",
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    tk = tokenizer if tokenizer is not None else count_tokens

    if mode == "by_file":
        sections = _split_to_sections(raw_content, "\n\n### ")
    elif mode == "by_paragraph":
        sections = _split_to_sections(raw_content, "\n\n")
    elif mode == "by_marker":
        sections = _split_to_sections(raw_content, marker)
    elif mode == "single":
        parts, was_truncated = _handle_single(raw_content, max_tokens, tokenizer=tk)
        if was_truncated:
            logger.warning(
                "Content truncated: %s tokens exceeds limit of %s tokens",
                tk(raw_content),
                max_tokens,
            )
        return parts
    else:
        sections = _split_to_sections(raw_content, "\n\n### ")

    return _build_parts(sections, max_tokens, separator=separator, tokenizer=tk)


def split_sections(
    sections: list[str],
    max_tokens: int,
    separator: str = "\n\n",
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """Split pre-built sections into token-limited parts.

    Unlike split(), this takes already-separated sections and packs
    them densely into parts without parsing a marker from raw content.
    """
    tk = tokenizer if tokenizer is not None else count_tokens
    return _build_parts(sections, max_tokens, separator=separator, tokenizer=tk)


def _split_to_sections(text: str, marker: str) -> list[str]:
    chunks = text.split(marker)
    result = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            if chunk.strip():
                result.append(chunk.strip())
        else:
            result.append(marker + chunk)
    return result


def _build_parts(
    sections: list[str],
    max_tokens: int,
    separator: str = "\n\n",
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    tk = tokenizer if tokenizer is not None else count_tokens

    parts = []
    current = ""
    current_tokens = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue
        section_tokens = tk(section)

        if section_tokens > max_tokens:
            if current:
                parts.append(current.strip())
                current = ""
                current_tokens = 0
            logger.warning(
                "Section too large: %s tokens exceeds limit of %s tokens, writing as-is",
                section_tokens,
                max_tokens,
            )
            parts.append(section)
            continue

        if current_tokens + section_tokens > max_tokens:
            parts.append(current.strip())
            current = section
            current_tokens = section_tokens
        else:
            if current:
                current += separator + section
            else:
                current = section
            current_tokens += section_tokens

    if current.strip():
        parts.append(current.strip())

    return parts


def _handle_single(
    text: str,
    max_tokens: int,
    tokenizer: Callable[[str], int] | None = None,
) -> tuple[list[str], bool]:
    """Split content into a single part, truncating if over limit.

    Uses tokenizer for accurate truncation instead of character-based estimate.
    Returns (parts, was_truncated).
    """
    tk = tokenizer if tokenizer is not None else count_tokens

    tokens = tk(text)
    if tokens <= max_tokens:
        return [text.strip()], False

    # Truncate using tokenizer — iterative halving for accuracy
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if tk(text[:mid]) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1

    text = text[:lo] + "\n\n# ... truncated ...\n"
    return [text.strip()], True


# ── Repo-map: signature extraction ─────────────────────────────────

# Language sets for dispatch — mirrors formatter.py
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

# C-like: match function/class/type signatures up to opening brace.
# [^{]* allows zero chars before { (e.g. "type Handler struct {").
_RE_C_LIKE_SIG = re.compile(
    r"^(\s*(?:export\s+)?(?:async\s+)?(?:function|def|class|interface|enum|struct|trait|impl|"
    r"type\s+\w+\s+\w+|type\s+|"
    r"public\s+class|public\s+static|public\s+function|"
    r"fn|func)\s+[^{]*)",
    re.MULTILINE,
)

# Ruby/Elixir/Lua: match def/function signatures
_RE_SCRIPT_SIG = re.compile(
    r"^(\s*(?:def\s+(?:self\.)?\w+[?!]?.*|"
    r"defmodule\s+[\w.]+.*|"
    r"defp\s+\w+.*|"
    r"function\s+\w+.*))",
    re.MULTILINE,
)


def extract_signatures(text: str, lang: str) -> str:
    """Extract only function/class signatures, strip bodies.

    Used for repo-map mode: gives AI an overview of the codebase
    without consuming tokens on implementation details.

    Args:
        text: full file content.
        lang: language from lang_for_path().

    Returns:
        Signatures-only text, or full text if language is unknown.
    """
    if lang == "python":
        return _extract_python_signatures(text)
    elif lang in _C_LIKE_LANGS or lang == "gdscript":
        return _extract_c_like_signatures(text)
    elif lang in _SCRIPT_LANGS:
        return _extract_script_signatures(text)
    # Fallback: return full file for unknown languages
    return text


def _extract_python_signatures(text: str) -> str:
    """Extract signatures from Python source using ast.

    Strips function/class bodies, replaces with '    ...'.
    Preserves decorators on the line before the definition.
    """
    import ast as _ast

    try:
        tree = _ast.parse(text)
    except SyntaxError:
        return text

    lines = text.split("\n")
    keep = [True] * len(lines)

    for node in _ast.iter_child_nodes(tree):
        if isinstance(node, (_ast.FunctionDef, _ast.ClassDef, _ast.AsyncFunctionDef)) and node.body:
            body_start = node.body[0].lineno - 1  # 0-indexed
            # Mark body lines for removal (keep signature + decorators)
            for i in range(body_start, node.end_lineno):
                keep[i] = False
            # Keep the signature line itself
            keep[node.lineno - 1] = True
            # Add placeholder after signature
            keep[body_start] = True
            lines[body_start] = "    ..."
            # Keep decorators
            for decorator in node.decorator_list:
                keep[decorator.lineno - 1] = True
            # If there's a return type annotation on its own line, keep it (FunctionDef only)
            if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)) and node.returns:
                keep[node.end_lineno - 1] = True

    result = "\n".join(line for i, line in enumerate(lines) if keep[i])
    return result.strip()


def _extract_c_like_signatures(text: str) -> str:
    """Extract signatures from C-like languages via regex.

    Matches function/class/method/type declarations up to {.
    Handles multi-line signatures by capturing until the brace.
    """
    sigs = []
    for m in _RE_C_LIKE_SIG.finditer(text):
        sig = m.group(1).strip()
        sigs.append(sig)

    if not sigs:
        return text

    return "\n".join(sigs)


def _extract_script_signatures(text: str) -> str:
    """Extract signatures from Ruby/Elixir/Lua via regex."""
    sigs = []
    for m in _RE_SCRIPT_SIG.finditer(text):
        sig = m.group(1).strip()
        sigs.append(sig)

    if not sigs:
        return text

    return "\n".join(sigs)


# ── End repo-map ───────────────────────────────────────────────────
