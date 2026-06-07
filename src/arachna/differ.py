"""LLM-optimized differ for Watch snapshots.

Generates human-readable diffs instead of unified diff format.
Uses difflib.SequenceMatcher to find changed blocks.

Markdown format (default, for chat):

    ### src/main.py

    REMOVED lines 45-47:
        total = 0
        for item in items:
            total += item.price

    ADDED lines 45:
        return sum(item.price for item in items)

XML format (for programmatic processing, --format xml):

    <file path="src/main.py">
      <removed>
        total = 0
        for item in items:
            total += item.price
      </removed>
      <added>
        return sum(item.price for item in items)
      </added>
    </file>
"""

import difflib
from dataclasses import dataclass
from xml.sax.saxutils import escape as _xml_escape

from .tokenizer import count_tokens


@dataclass
class DiffSection:
    """A single file change in a diff."""

    type: str  # "modified" | "added" | "deleted" | "renamed" | "moved"
    path: str
    content: str = ""
    old_path: str | None = None  # for rename/move: previous path
    similarity: float | None = None  # 0.0-1.0 for rename/move detection


def compute_diff(
    old_content: str,
    new_content: str,
    path: str,
    fmt: str = "markdown",
) -> str:
    """Compute LLM-friendly diff between two file versions.

    Args:
        old_content: file content in the snapshot.
        new_content: current file content.
        path: file path for the header.
        fmt: "markdown" or "xml".

    Returns:
        Formatted diff string, or empty string if unchanged.
    """
    if old_content == new_content:
        return ""

    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    if not old_lines and new_lines:
        return _format_added(path, new_content, fmt)

    if old_lines and not new_lines:
        return _format_deleted(path, fmt)

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    blocks = matcher.get_opcodes()

    removed_parts = []
    added_parts = []

    for tag, i1, i2, j1, j2 in blocks:
        if tag == "replace":
            removed_parts.append(_format_line_range(i1, i2, old_lines))
            added_parts.append(_format_line_range(j1, j2, new_lines))
        elif tag == "delete":
            removed_parts.append(_format_line_range(i1, i2, old_lines))
        elif tag == "insert":
            added_parts.append(_format_line_range(j1, j2, new_lines))

    if not removed_parts and not added_parts:
        return ""

    if fmt == "xml":
        return _format_xml_diff(path, removed_parts, added_parts)
    return _format_markdown_diff(path, removed_parts, added_parts)


def _format_line_range(start: int, end: int, lines: list[str]) -> str:
    """Format a range of lines: 'lines 45-47:\\n    ...'"""
    if start == end:
        return ""
    line_nums = f"lines {start + 1}"
    if end > start + 1:
        line_nums += f"-{end}"
    content = "".join(lines[start:end]).rstrip("\n")
    indented = "\n".join(f"    {line}" for line in content.split("\n"))
    return f"{line_nums}:\n{indented}"


def _format_markdown_diff(
    path: str,
    removed_parts: list[str],
    added_parts: list[str],
) -> str:
    """Format diff in markdown."""
    lines = [f"### {path}\n"]
    for part in removed_parts:
        lines.append(f"REMOVED {part}\n")
    for part in added_parts:
        lines.append(f"ADDED {part}\n")
    return "\n".join(lines)


def _format_xml_diff(
    path: str,
    removed_parts: list[str],
    added_parts: list[str],
) -> str:
    """Format diff in XML with proper escaping."""
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


def _format_added(path: str, content: str, fmt: str) -> str:
    """Format a newly added file."""
    if fmt == "xml":
        escaped_path = _xml_escape(path)
        return f'<file path="{escaped_path}">\n  <added>\n    {_xml_escape(content)}\n  </added>\n</file>\n'
    return f"### {path}\n\nADDED (new file):\n\n```\n{content}\n```\n"


def _format_deleted(path: str, fmt: str) -> str:
    """Format a deleted file."""
    if fmt == "xml":
        escaped_path = _xml_escape(path)
        return f'<file path="{escaped_path}">\n  <removed>\n    [DELETED]\n  </removed>\n</file>\n'
    return f"### {path}\n\n[DELETED]\n"


def compute_diff_stats(diffs: list[DiffSection]) -> dict:
    """Return aggregate statistics for a list of DiffSections.

    Returns:
        {modified: N, added: N, deleted: N, renamed: N, moved: N, tokens: N}
    """
    modified = 0
    added = 0
    deleted = 0
    renamed = 0
    moved = 0
    tokens = 0

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
