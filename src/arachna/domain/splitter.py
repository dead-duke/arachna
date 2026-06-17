# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Split content into token-limited parts + signature extraction."""

import ast as _ast
import logging
import re

from .formatter import C_LIKE_LANGS, SCRIPT_LANGS
from .tokenizer import count_tokens

logger = logging.getLogger("arachna.splitter")
_MAX_TRUNCATION_ITERATIONS = 100


def _pack_chunks(current, current_tokens, item, item_tokens, max_tokens, chunks, sep):
    if item_tokens > max_tokens:
        if current:
            chunks.append(current)
        chunks.append(item)
        return "", 0
    if current_tokens + item_tokens > max_tokens and current:
        chunks.append(current)
        return item, item_tokens
    return (current + sep + item if current else item), current_tokens + item_tokens


def _split_by_sep(section, max_tokens, tokenizer, sep):
    items = section.split(sep)
    if len(items) <= 1:
        return []
    chunks = []
    current = ""
    current_tokens = 0
    for item in items:
        current, current_tokens = _pack_chunks(
            current, current_tokens, item, tokenizer(item), max_tokens, chunks, sep
        )
    if current:
        chunks.append(current)
    return chunks if len(chunks) > 1 else []


def _split_by_paragraphs(s, m, t):
    return _split_by_sep(s, m, t, "\n\n")


def _split_by_lines(s, m, t):
    return _split_by_sep(s, m, t, "\n")


def _split_by_char_boundary(section, max_tokens, tokenizer):
    logger.warning(
        "Splitting oversized section at character boundary (no paragraph/line breaks found)"
    )
    chunks = []
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


def _split_oversized_section(section, max_tokens, tokenizer):
    for method in (_split_by_paragraphs, _split_by_lines):
        chunks = method(section, max_tokens, tokenizer)
        if chunks:
            return chunks
    return _split_by_char_boundary(section, max_tokens, tokenizer)


def _add_continuation_markers(chunks, base_part_num):
    if len(chunks) <= 1:
        return chunks
    result = []
    for j, chunk in enumerate(chunks):
        if j == 0:
            chunk += f"\n\n> **[CONTINUES in part {base_part_num + 2}]**"
        elif j == len(chunks) - 1:
            chunk = f"> **[CONTINUED from part {base_part_num}]**\n\n{chunk}"
        else:
            chunk = (
                f"> **[CONTINUED from part {base_part_num}]**\n\n{chunk}"
                f"\n\n> **[CONTINUES in part {base_part_num + 2}]**"
            )
        result.append(chunk.strip())
    return result


def _handle_oversized_section(
    section, i, max_tokens, tk, current, current_tokens, current_indices, parts, indices
):
    if current:
        parts.append(current.strip())
        indices.append(current_indices)
    chunks = _split_oversized_section(section, max_tokens, tokenizer=tk)
    logger.warning(
        "Section too large: %s tokens exceeds limit of %s tokens, split into %s parts",
        tk(section),
        max_tokens,
        len(chunks),
    )
    for chunk in _add_continuation_markers(chunks, len(parts)):
        parts.append(chunk)
        indices.append([i])
    return "", 0, []


def _pack_section_into_parts(sections, max_tokens, separator, tk):
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
            current, current_tokens, current_indices = _handle_oversized_section(
                section, i, max_tokens, tk, current, current_tokens, current_indices, parts, indices
            )
            continue
        if current_tokens + section_tokens > max_tokens:
            parts.append(current.strip())
            indices.append(current_indices)
            current = section
            current_tokens = section_tokens
            current_indices = [i]
        else:
            current = current + separator + section if current else section
            current_tokens += section_tokens
            current_indices.append(i)
    if current.strip():
        parts.append(current.strip())
        indices.append(current_indices)
    return parts, indices


def pack_into_parts(sections, max_tokens, separator="\n\n", tokenizer=None):
    tk = tokenizer if tokenizer is not None else count_tokens
    if max_tokens == -1:
        all_content = separator.join(s.strip() for s in sections if s.strip())
        return [all_content], [list(range(len(sections)))]
    return _pack_section_into_parts(sections, max_tokens, separator, tk)


def _build_parts_for_sections(sections, max_tokens, separator, tk):
    """Pack sections into token-limited parts with truncation for oversized sections."""
    if max_tokens == -1:
        content = separator.join(s.strip() for s in sections if s.strip())
        return [content] if content else []
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
            current = current + separator + section if current else section
            current_tokens += section_tokens
    if current.strip():
        parts.append(current.strip())
    return parts


def _split_by_file(r, m, mrk, sep, tk):
    return _build_parts_for_sections(_split_to_sections(r, "\n\n### "), m, sep, tk)


def _split_by_paragraph(r, m, mrk, sep, tk):
    return _build_parts_for_sections(_split_to_sections(r, "\n\n"), m, sep, tk)


def _split_by_marker(r, m, mrk, sep, tk):
    return _build_parts_for_sections(_split_to_sections(r, mrk), m, sep, tk)


def _split_single(raw_content, max_tokens, marker, separator, tk):
    parts, was_truncated = _handle_single(raw_content, max_tokens, tokenizer=tk)
    if was_truncated:
        logger.warning(
            "Content truncated: %s tokens exceeds limit of %s tokens",
            tk(raw_content),
            max_tokens,
        )
    return parts


_SPLIT_MODE_DISPATCH = {
    "by_file": _split_by_file,
    "by_paragraph": _split_by_paragraph,
    "by_marker": _split_by_marker,
    "single": _split_single,
}


def split(raw_content, max_tokens, mode="by_file", marker="\n\n", separator="\n\n", tokenizer=None):
    tk = tokenizer if tokenizer is not None else count_tokens
    if max_tokens == -1:
        return [raw_content.strip()] if raw_content.strip() else []
    handler = _SPLIT_MODE_DISPATCH.get(mode, _split_by_file)
    return handler(raw_content, max_tokens, marker, separator, tk)


def split_sections(sections, max_tokens, separator="\n\n", tokenizer=None):
    return pack_into_parts(sections, max_tokens, separator=separator, tokenizer=tokenizer)


def _split_to_sections(text, marker):
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


def _handle_single(text, max_tokens, tokenizer=None):
    tk = tokenizer if tokenizer is not None else count_tokens
    tokens = tk(text)
    if tokens <= max_tokens:
        return [text.strip()], False
    if tk is count_tokens:
        return [text[: max_tokens * 4] + "\n\n# ... truncated ...\n".strip()], True
    lo, hi = 0, len(text)
    iterations = 0
    while lo < hi and iterations < _MAX_TRUNCATION_ITERATIONS:
        iterations += 1
        mid = (lo + hi + 1) // 2
        if tk(text[:mid]) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1
    return [text[:lo] + "\n\n# ... truncated ...\n".strip()], True


_RE_C_LIKE_SIG = re.compile(
    r"^(\s*(?:export\s+)?(?:async\s+)?(?:function|def|class|interface|enum|struct|trait|impl|"
    r"type\s+\w+\s+\w+|type\s+|public\s+class|public\s+static|public\s+function|fn|func)\s+[^{]*)",
    re.MULTILINE,
)
_RE_SCRIPT_SIG = re.compile(
    r"^(\s*(?:def\s+(?:self\.)?\w+[?!]?.*|defmodule\s+[\w.]+.*|defp\s+\w+.*|function\s+\w+.*))",
    re.MULTILINE,
)


def _extract_python_node(node, lines, keep):
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


def _extract_python_signatures(text):
    try:
        tree = _ast.parse(text)
    except SyntaxError:
        return text
    lines = text.split("\n")
    keep = [True] * len(lines)
    for node in _ast.iter_child_nodes(tree):
        if isinstance(node, (_ast.FunctionDef, _ast.ClassDef, _ast.AsyncFunctionDef)) and node.body:
            _extract_python_node(node, lines, keep)
    return "\n".join(line for i, line in enumerate(lines) if keep[i]).strip()


def _extract_c_like_signatures(text):
    sigs = [m.group(1).strip() for m in _RE_C_LIKE_SIG.finditer(text)]
    return "\n".join(sigs) if sigs else text


def _extract_script_signatures(text):
    sigs = [m.group(1).strip() for m in _RE_SCRIPT_SIG.finditer(text)]
    return "\n".join(sigs) if sigs else text


def _build_sig_extractors():
    extractors = {"python": _extract_python_signatures, "gdscript": _extract_c_like_signatures}
    for lang in C_LIKE_LANGS:
        extractors[lang] = _extract_c_like_signatures
    for lang in SCRIPT_LANGS:
        extractors[lang] = _extract_script_signatures
    return extractors


_SIG_EXTRACTORS = _build_sig_extractors()


def extract_signatures(text, lang):
    return _SIG_EXTRACTORS.get(lang, lambda t: t)(text)
