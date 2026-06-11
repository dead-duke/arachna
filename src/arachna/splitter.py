# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Split content into token-limited parts + signature extraction."""

import logging
import re
from collections.abc import Callable

from .formatter import C_LIKE_LANGS, SCRIPT_LANGS
from .tokenizer import count_tokens

logger = logging.getLogger("arachna.splitter")

_MAX_TRUNCATION_ITERATIONS = 100


def _split_oversized_section(
    section: str,
    max_tokens: int,
    tokenizer: Callable[[str], int],
) -> list[str]:
    """Split an oversized section into chunks that each fit max_tokens.

    Fallback chain: paragraphs -> lines -> character boundary.
    Returns: list of raw content chunks (without continuation markers).
    Guarantees: len(chunks) >= 2, all chunks fit max_tokens (except single-line fallback).
    """
    chunks = []

    # Level 1: Try splitting by paragraphs (double newlines)
    paragraphs = section.split("\n\n")
    if len(paragraphs) > 1:
        current = ""
        current_tokens = 0
        for para in paragraphs:
            para_tokens = tokenizer(para)
            # If paragraph itself exceeds limit, flush current and add as chunk
            if para_tokens > max_tokens:
                if current:
                    chunks.append(current)
                    current = ""
                    current_tokens = 0
                chunks.append(para)
                continue
            if current_tokens + para_tokens > max_tokens and current:
                chunks.append(current)
                current = para
                current_tokens = para_tokens
            else:
                if current:
                    current += "\n\n" + para
                else:
                    current = para
                current_tokens += para_tokens
        if current:
            chunks.append(current)
        if len(chunks) > 1:
            return chunks

    # Level 2: Try splitting by lines (single newlines)
    lines = section.split("\n")
    if len(lines) > 1:
        current = ""
        current_tokens = 0
        for line in lines:
            line_tokens = tokenizer(line)
            # If line itself exceeds limit, flush current and add as chunk
            if line_tokens > max_tokens:
                if current:
                    chunks.append(current)
                    current = ""
                    current_tokens = 0
                chunks.append(line)
                continue
            if current_tokens + line_tokens > max_tokens and current:
                chunks.append(current)
                current = line
                current_tokens = line_tokens
            else:
                if current:
                    current += "\n" + line
                else:
                    current = line
                current_tokens += line_tokens
        if current:
            chunks.append(current)
        if len(chunks) > 1:
            return chunks

    # Level 3: Character boundary fallback (single line or minified code)
    logger.warning(
        "Splitting oversized section at character boundary (no paragraph/line breaks found)"
    )
    remaining = section
    while remaining:
        if tokenizer(remaining) <= max_tokens:
            chunks.append(remaining)
            break
        lo, hi = 0, len(remaining)
        iterations = 0
        while lo < hi and iterations < _MAX_TRUNCATION_ITERATIONS:
            iterations += 1
            mid = (lo + hi + 1) // 2
            if tokenizer(remaining[:mid]) <= max_tokens:
                lo = mid
            else:
                hi = mid - 1
        chunks.append(remaining[:lo])
        remaining = remaining[lo:]
    return chunks


def pack_into_parts(
    sections: list[str],
    max_tokens: int,
    separator: str = "\n\n",
    tokenizer: Callable[[str], int] | None = None,
) -> tuple[list[str], list[list[int]]]:
    """Single token-packing primitive — packs formatted sections into token-limited parts.

    Handles oversized sections via _split_oversized_section with
    continuation markers. Each chunk shares the original section index.

    For formatted file sections where splitting oversized content
    into chunks is meaningful (split_sections, _stream_full_mode).

    Returns (parts, indices) where indices[i] = list of section positions
    packed into parts[i]. Indices may contain duplicates for split sections.
    """
    tk = tokenizer if tokenizer is not None else count_tokens
    parts = []
    indices = []
    current = ""
    current_tokens = 0
    current_indices = []

    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue
        section_tokens = tk(section)

        if section_tokens > max_tokens:
            # Flush current part before splitting oversized section
            if current:
                parts.append(current.strip())
                indices.append(current_indices)
                current = ""
                current_tokens = 0
                current_indices = []

            # Split oversized section
            chunks = _split_oversized_section(section, max_tokens, tokenizer=tk)
            logger.warning(
                "Section too large: %s tokens exceeds limit of %s tokens, split into %s parts",
                section_tokens,
                max_tokens,
                len(chunks),
            )

            # Add continuation markers
            for j, chunk in enumerate(chunks):
                if len(chunks) > 1:
                    if j == 0:
                        chunk += f"\n\n> **[CONTINUES in part {len(parts) + 2}]**"
                    elif j == len(chunks) - 1:
                        chunk = f"> **[CONTINUED from part {len(parts)}]**\n\n{chunk}"
                    else:
                        chunk = (
                            f"> **[CONTINUED from part {len(parts)}]**\n\n{chunk}"
                            f"\n\n> **[CONTINUES in part {len(parts) + 2}]**"
                        )
                parts.append(chunk.strip())
                indices.append([i])
            continue

        if current_tokens + section_tokens > max_tokens:
            parts.append(current.strip())
            indices.append(current_indices)
            current = section
            current_tokens = section_tokens
            current_indices = [i]
        else:
            if current:
                current += separator + section
            else:
                current = section
            current_tokens += section_tokens
            current_indices.append(i)

    if current.strip():
        parts.append(current.strip())
        indices.append(current_indices)

    return parts, indices


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
) -> tuple[list[str], list[list[int]]]:
    """Split pre-built sections into token-limited parts.

    Thin wrapper around pack_into_parts — for formatted file sections
    where oversized content can be split into chunks.
    """
    return pack_into_parts(sections, max_tokens, separator=separator, tokenizer=tokenizer)


def _split_to_sections(text: str, marker: str) -> list[str]:
    if not text:
        return []
    if text.startswith(marker):
        rest = text[len(marker) :]
        chunks = rest.split(marker)
        result = [marker + chunks[0]]
        for chunk in chunks[1:]:
            if chunk.strip():
                result.append(marker + chunk)
        return result
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
    """Pack raw content sections into token-limited parts.

    For command mode — oversized sections are truncated via _handle_single.
    Unlike pack_into_parts which splits oversized sections into chunks,
    this truncates them since raw command output can't be meaningfully split.
    """
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
            truncated, _ = _handle_single(section, max_tokens, tokenizer=tk)
            logger.warning(
                "Section too large: %s tokens exceeds limit of %s tokens, truncated",
                section_tokens,
                max_tokens,
            )
            parts.extend(truncated)
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
    tk = tokenizer if tokenizer is not None else count_tokens
    tokens = tk(text)
    if tokens <= max_tokens:
        return [text.strip()], False
    if tk is count_tokens:
        limit = max_tokens * 4
        text = text[:limit] + "\n\n# ... truncated ...\n"
        return [text.strip()], True
    lo, hi = 0, len(text)
    iterations = 0
    while lo < hi and iterations < _MAX_TRUNCATION_ITERATIONS:
        iterations += 1
        mid = (lo + hi + 1) // 2
        if tk(text[:mid]) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1
    text = text[:lo] + "\n\n# ... truncated ...\n"
    return [text.strip()], True


_RE_C_LIKE_SIG = re.compile(
    r"^(\s*(?:export\s+)?(?:async\s+)?(?:function|def|class|interface|enum|struct|trait|impl|"
    r"type\s+\w+\s+\w+|type\s+|"
    r"public\s+class|public\s+static|public\s+function|"
    r"fn|func)\s+[^{]*)",
    re.MULTILINE,
)

_RE_SCRIPT_SIG = re.compile(
    r"^(\s*(?:def\s+(?:self\.)?\w+[?!]?.*|"
    r"defmodule\s+[\w.]+.*|"
    r"defp\s+\w+.*|"
    r"function\s+\w+.*))",
    re.MULTILINE,
)


def extract_signatures(text: str, lang: str) -> str:
    if lang == "python":
        return _extract_python_signatures(text)
    elif lang in C_LIKE_LANGS or lang == "gdscript":
        return _extract_c_like_signatures(text)
    elif lang in SCRIPT_LANGS:
        return _extract_script_signatures(text)
    return text


def _extract_python_signatures(text: str) -> str:
    import ast as _ast

    try:
        tree = _ast.parse(text)
    except SyntaxError:
        return text
    lines = text.split("\n")
    keep = [True] * len(lines)
    for node in _ast.iter_child_nodes(tree):
        if isinstance(node, (_ast.FunctionDef, _ast.ClassDef, _ast.AsyncFunctionDef)) and node.body:
            body_start = node.body[0].lineno - 1
            for i in range(body_start, node.end_lineno):
                keep[i] = False
            keep[node.lineno - 1] = True
            keep[body_start] = True
            lines[body_start] = "    ..."
            for decorator in node.decorator_list:
                keep[decorator.lineno - 1] = True
            if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)) and node.returns:
                keep[node.end_lineno - 1] = True
    result = "\n".join(line for i, line in enumerate(lines) if keep[i])
    return result.strip()


def _extract_c_like_signatures(text: str) -> str:
    sigs = []
    for m in _RE_C_LIKE_SIG.finditer(text):
        sig = m.group(1).strip()
        sigs.append(sig)
    return "\n".join(sigs) if sigs else text


def _extract_script_signatures(text: str) -> str:
    sigs = []
    for m in _RE_SCRIPT_SIG.finditer(text):
        sig = m.group(1).strip()
        sigs.append(sig)
    return "\n".join(sigs) if sigs else text
