# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""LLM-optimized differ for snapshots."""

import difflib
import logging
from xml.sax.saxutils import escape as _xml_escape

from ..domain.api_types import DiffSection
from ..domain.tokenizer import count_tokens

logger = logging.getLogger("arachna.differ")


def _build_diff_blocks(old_lines, new_lines, line_numbers=False):
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    blocks = matcher.get_opcodes()
    removed_parts = []
    added_parts = []
    for tag, i1, i2, j1, j2 in blocks:
        if tag == "replace":
            removed_parts.append(_format_line_range(i1, i2, old_lines, line_numbers=line_numbers))
            added_parts.append(_format_line_range(j1, j2, new_lines, line_numbers=line_numbers))
        elif tag == "delete":
            removed_parts.append(_format_line_range(i1, i2, old_lines, line_numbers=line_numbers))
        elif tag == "insert":
            added_parts.append(_format_line_range(j1, j2, new_lines, line_numbers=line_numbers))
    return removed_parts, added_parts


def compute_diff(
    old_content: str,
    new_content: str,
    path: str,
    fmt: str = "markdown",
    max_tokens: int | None = None,
    tokenizer=None,
    line_numbers: bool = False,
) -> str:
    if old_content == new_content:
        return ""
    tk = tokenizer if tokenizer is not None else count_tokens
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    if not old_lines and new_lines:
        return _format_added(
            path, new_content, fmt, max_tokens=max_tokens, tokenizer=tk, line_numbers=line_numbers
        )
    if old_lines and not new_lines:
        return _format_deleted(path, fmt)
    removed_parts, added_parts = _build_diff_blocks(old_lines, new_lines, line_numbers=line_numbers)
    if not removed_parts and not added_parts:
        return ""
    if fmt == "xml":
        return _format_xml_diff(path, removed_parts, added_parts)
    return _format_markdown_diff(path, removed_parts, added_parts)


def _format_line_range(start: int, end: int, lines: list[str], line_numbers: bool = False) -> str:
    if start == end:
        return ""
    line_nums = f"lines {start + 1}"
    if end > start + 1:
        line_nums += f"-{end}"
    content = "".join(lines[start:end]).rstrip("\n")
    if line_numbers:
        content_lines = content.split("\n")
        width = max(5, len(str(end)))
        numbered = [f"{i + 1:>{width}}| {line}" for i, line in enumerate(content_lines, start)]
        indented = "\n".join(f"    {line}" for line in numbered)
    else:
        indented = "\n".join(f"    {line}" for line in content.split("\n"))
    return f"{line_nums}:\n{indented}"


def _format_markdown_diff(path: str, removed_parts: list[str], added_parts: list[str]) -> str:
    lines = [f"### {path}\n"]
    for part in removed_parts:
        lines.append(f"REMOVED {part}\n")
    for part in added_parts:
        lines.append(f"ADDED {part}\n")
    return "\n".join(lines)


def _format_xml_diff(path: str, removed_parts: list[str], added_parts: list[str]) -> str:
    escaped_path = _xml_escape(path)
    lines = [f'<file path="{escaped_path}">']
    if removed_parts:
        lines.append("  <removed>")
        for part in removed_parts:
            content = part.split("\n", 1)[1] if "\n" in part else part
            lines.append(f"    {_xml_escape(content)}")
        lines.append("  </removed>")
    if added_parts:
        lines.append("  <added>")
        for part in added_parts:
            content = part.split("\n", 1)[1] if "\n" in part else part
            lines.append(f"    {_xml_escape(content)}")
        lines.append("  </added>")
    lines.append("</file>\n")
    return "\n".join(lines)


def _truncate_if_needed(content: str, max_tokens: int, tk) -> str:
    if tk(content) <= max_tokens:
        return content
    truncation_msg = "\n# ... truncated (exceeds token limit) ...\n"
    lo, hi = 0, len(content)
    iterations = 0
    while lo < hi and iterations < 100:
        iterations += 1
        mid = (lo + hi + 1) // 2
        if tk(content[:mid] + truncation_msg) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1
    return content[:lo] + truncation_msg


def _format_added(
    path: str,
    content: str,
    fmt: str,
    max_tokens: int | None = None,
    tokenizer=None,
    line_numbers: bool = False,
) -> str:
    tk = tokenizer if tokenizer is not None else count_tokens
    if max_tokens is not None and tk(content) > max_tokens:
        content = _truncate_if_needed(content, max_tokens, tk)
        logger.warning("Added file exceeds max_tokens=%s — truncated", max_tokens)
    if line_numbers and content.strip():
        lines = content.rstrip("\n").split("\n")
        width = max(5, len(str(len(lines))))
        content = "\n".join(f"{i:>{width}}| {line}" for i, line in enumerate(lines, 1))
    if fmt == "xml":
        escaped_path = _xml_escape(path)
        return f'<file path="{escaped_path}">\n  <added>\n    {_xml_escape(content)}\n  </added>\n</file>\n'
    return f"### {path}\n\nADDED (new file):\n\n```\n{content}\n```\n"


def _format_deleted(path: str, fmt: str) -> str:
    if fmt == "xml":
        escaped_path = _xml_escape(path)
        return f'<file path="{escaped_path}">\n  <removed>\n    [DELETED]\n  </removed>\n</file>\n'
    return f"### {path}\n\n[DELETED]\n"


def compute_diff_stats(diffs: list[DiffSection]) -> dict:
    modified = added = deleted = renamed = moved = tokens = 0
    for d in diffs:
        if d.type == "modified":
            modified += 1
        elif d.type == "added":
            added += 1
        elif d.type == "deleted":
            deleted += 1
        elif d.type == "renamed":
            renamed += 1
        elif d.type == "moved":
            moved += 1
        tokens += count_tokens(d.content)
    return {
        "modified": modified,
        "added": added,
        "deleted": deleted,
        "renamed": renamed,
        "moved": moved,
        "tokens": tokens,
    }
