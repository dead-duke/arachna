"""Structural diff — understands code blocks, not just text lines.

For Python: uses ast to parse source into named blocks (functions,
classes, async functions) and compares them by name.
For C-like languages (JS/TS/Go/Rust/Java/C/C++/C#/Swift/Kotlin/PHP/Zig/Gleam):
uses regex to find function/class/method declarations with brace
matching for body extraction.
For Ruby/Elixir/Lua: regex-based block parsing.
For all other languages: falls back to text-based difflib.

Used by --mode structural in --diff CLI and compute_diff() API.

Main entry points:
    structural_diff_sections(sections, fmt) -> list[DiffSection]
    structural_diff_for_lang(old, new, path, lang, fmt) -> str
    structural_diff(old, new, path, lang, fmt) -> str
"""

import re
from pathlib import Path

from .formatter import C_LIKE_LANGS, SCRIPT_LANGS, lang_for_path


def structural_diff_sections(sections: list, fmt: str = "markdown") -> list:
    """Apply structural diff to a list of DiffSections from watcher."""
    result = []
    for s in sections:
        if s.type != "modified" or not s.path:
            result.append(s)
            continue
        lang = lang_for_path(Path(s.path))
        old_content, new_content = _extract_old_new_from_section(s.content)
        if old_content is not None and new_content is not None:
            structural = structural_diff_for_lang(old_content, new_content, s.path, lang, fmt)
            if structural.strip():
                s.content = structural
        result.append(s)
    return result


def structural_diff_for_lang(
    old_content: str, new_content: str, path: str, lang: str, fmt: str = "markdown"
) -> str:
    """Compute block-level structural diff between two file versions.

    Single dispatch entry point — used by both differ_structural and watch.py.
    """
    if lang == "python":
        blocks_old = _parse_python_blocks(old_content)
        blocks_new = _parse_python_blocks(new_content)
    elif lang in C_LIKE_LANGS or lang == "gdscript":
        blocks_old = _parse_c_like_blocks(old_content, lang)
        blocks_new = _parse_c_like_blocks(new_content, lang)
    elif lang in SCRIPT_LANGS:
        blocks_old = _parse_script_blocks(old_content)
        blocks_new = _parse_script_blocks(new_content)
    else:
        return _fallback_diff(old_content, new_content, path, fmt)
    return _format_block_diff(blocks_old, blocks_new, path, fmt)


def structural_diff(
    old_content: str, new_content: str, path: str, lang: str, fmt: str = "markdown"
) -> str:
    """Deprecated: use structural_diff_for_lang() instead."""
    return structural_diff_for_lang(old_content, new_content, path, lang, fmt)


def _extract_old_new_from_section(content: str) -> tuple[str | None, str | None]:
    """Parse a markdown diff section into old and new content."""
    old_lines = []
    new_lines = []
    in_removed = False
    in_added = False
    for line in content.split("\n"):
        if line.startswith("REMOVED "):
            in_removed, in_added = True, False
            continue
        elif line.startswith("ADDED "):
            in_removed, in_added = False, True
            continue
        elif (
            line.startswith("### ")
            or line.startswith("[DELETED]")
            or line.startswith("RENAMED")
            or line.startswith("MOVED")
        ):
            in_removed, in_added = False, False
            continue
        if in_removed:
            stripped = line[4:] if line.startswith("    ") else line
            old_lines.append(stripped)
        elif in_added:
            stripped = line[4:] if line.startswith("    ") else line
            new_lines.append(stripped)
    if not old_lines and not new_lines:
        return None, None
    return "\n".join(old_lines), "\n".join(new_lines)


# ── Python block parsing (ast) ─────────────────────────────────────


def _parse_python_blocks(text: str) -> dict[str, tuple[str, str]]:
    """Parse Python source into {name: (signature, body)} blocks."""
    import ast as _ast

    try:
        tree = _ast.parse(text)
    except SyntaxError:
        return {}
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


# ── C-like block parsing (regex with named groups) ─────────────────

_RE_C_LIKE_BLOCK = re.compile(
    r"^("
    r"\s*(?:export\s+)?(?:async\s+)?function\s+(?P<name>\w+)[^{]*"
    r"|"
    r"\s*def\s+(?P<name2>\w+)[^{]*"
    r"|"
    r"\s*(?:export\s+)?(?:async\s+)?class\s+(?P<name3>\w+)[^{]*"
    r"|"
    r"\s*(?:export\s+)?(?:async\s+)?interface\s+(?P<name4>\w+)[^{]*"
    r"|"
    r"\s*(?:export\s+)?(?:async\s+)?enum\s+(?P<name5>\w+)[^{]*"
    r"|"
    r"\s*(?:export\s+)?(?:async\s+)?struct\s+(?P<name6>\w+)[^{]*"
    r"|"
    r"\s*(?:export\s+)?(?:async\s+)?trait\s+(?P<name7>\w+)[^{]*"
    r"|"
    r"\s*(?:export\s+)?(?:async\s+)?impl\s+(?P<name8>\w+)[^{]*"
    r"|"
    r"\s*type\s+(?P<name9>\w+)\s+\w+[^{]*"  # type Handler struct {
    r"|"
    r"\s*type\s+(?P<name10>\w+)[^{]*"  # type MyInt int
    r"|"
    r"\s*public\s+class\s+(?P<name11>\w+)[^{]*"
    r"|"
    r"\s*public\s+static\s+(?P<name12>\w+)[^{]*"
    r"|"
    r"\s*public\s+function\s+(?P<name13>\w+)[^{]*"
    r"|"
    r"\s*fn\s+(?P<name14>\w+)[^{]*"
    r"|"
    r"\s*func\s+(?P<name15>\w+)[^{]*"
    r")",
    re.MULTILINE,
)

# Map group index to name group key — name15 maps to "name15", etc.
_C_LIKE_NAME_GROUPS = [f"name{i}" if i > 1 else "name" for i in range(1, 16)]
_C_LIKE_NAME_GROUPS[0] = "name"  # group 1 uses "name"
_C_LIKE_NAME_GROUPS[1] = "name2"  # group 2 uses "name2"
# Actually: named groups are indexed by their position in the regex.
# "name" is group 1, "name2" is group 2, ..., "name15" is group 15.
# In Python re, named groups are numbered sequentially among all groups.
# So: name=1, name2=2, name3=3, ..., name15=15.


def _parse_c_like_blocks(text: str, lang: str) -> dict[str, tuple[str, str]]:
    """Parse C-like source into {name: (signature, body)} blocks.

    Uses a single regex with named capture groups for each declaration type.
    Sig = full match (group 0). Name = the one named group that matched.
    Bodies are extracted via brace matching.
    """
    blocks = {}
    for m in _RE_C_LIKE_BLOCK.finditer(text):
        sig = m.group(0).strip()
        # Find which named group matched
        name = None
        for group_name in [
            "name",
            "name2",
            "name3",
            "name4",
            "name5",
            "name6",
            "name7",
            "name8",
            "name9",
            "name10",
            "name11",
            "name12",
            "name13",
            "name14",
            "name15",
        ]:
            try:
                name = m.group(group_name)
                if name is not None:
                    break
            except IndexError:
                continue

        if name is None:
            continue

        body_start = m.end()
        if body_start < len(text) and text[body_start] == "{":
            body = _extract_braced_block(text, body_start)
        else:
            body = ""
        blocks[name] = (sig, body)
    return blocks


def _extract_braced_block(text: str, start: int) -> str:
    """Extract text from opening brace to matching closing brace."""
    if start >= len(text) or text[start] != "{":
        return ""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
        i += 1
    return text[start:]


# ── Script block parsing (regex) ───────────────────────────────────


def _parse_script_blocks(text: str) -> dict[str, tuple[str, str]]:
    """Parse Ruby/Elixir/Lua source into {name: (signature, body)} blocks."""
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


# ── Diff formatting ────────────────────────────────────────────────


def _format_block_diff(old_blocks: dict, new_blocks: dict, path: str, fmt: str) -> str:
    """Compare two block dicts and produce formatted structural diff."""
    all_names = set(old_blocks.keys()) | set(new_blocks.keys())
    parts = [f"### {path}\n"]
    for name in sorted(all_names):
        old = old_blocks.get(name)
        new = new_blocks.get(name)
        if old is None and new is not None:
            sig, body = new
            parts.append(f"ADDED: {_block_label(name, sig)}\n")
            parts.append(f"{sig}\n{body}\n\n")
        elif old is not None and new is None:
            sig, _body = old
            parts.append(f"DELETED: {_block_label(name, sig)}\n\n")
        elif old is not None and new is not None:
            old_sig, old_body = old
            new_sig, new_body = new
            sig_changed = old_sig != new_sig
            body_changed = old_body != new_body
            if not sig_changed and not body_changed:
                continue
            parts.append(f"MODIFIED: {_block_label(name, old_sig)}\n")
            if sig_changed:
                parts.append("  Signature changed:\n")
                parts.append(f"    - {old_sig}\n")
                parts.append(f"    + {new_sig}\n")
            if body_changed:
                parts.append("  Body:\n")
                body_diff = _fallback_diff(old_body, new_body, "", fmt)
                if body_diff.strip():
                    for line in body_diff.split("\n"):
                        if line.strip():
                            parts.append(f"    {line}\n")
            parts.append("\n")
    return "".join(parts)


def _block_label(name: str, signature: str) -> str:
    """Generate a human-readable label for a code block."""
    if signature.startswith("class ") or signature.startswith("interface "):
        return f"class {name}"
    elif (
        signature.startswith("def ")
        or signature.startswith("function ")
        or signature.startswith("func ")
        or signature.startswith("fn ")
    ):
        return f"function {name}"
    else:
        return name


def _fallback_diff(old: str, new: str, path: str, fmt: str) -> str:
    """Fallback to text-based difflib diff for unknown languages."""
    from .differ import compute_diff

    if not old and not new:
        return ""
    return compute_diff(old, new, path, fmt=fmt)
