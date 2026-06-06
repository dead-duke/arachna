"""Structural diff — understands code blocks, not just text lines.

For Python: uses ast to parse source into named blocks (functions,
classes, async functions) and compares them by name.
For C-like languages (JS/TS/Go/Rust/Java/C/C++/C#/Swift/Kotlin/PHP):
uses regex to find function/class/method declarations with brace
matching for body extraction.
For Ruby/Elixir/Lua: regex-based block parsing.
For all other languages: falls back to text-based difflib.

Used by --mode structural in --diff CLI and compute_diff() API.

Main entry points:
    structural_diff_sections(sections, fmt) -> list[DiffSection]
    structural_diff(old, new, path, lang, fmt) -> str
"""

import re
from pathlib import Path

from .formatter import lang_for_path

# Language sets for dispatch — mirrors formatter.py and splitter.py
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


def structural_diff_sections(sections: list, fmt: str = "markdown") -> list:
    """Apply structural diff to a list of DiffSections from watcher.

    Iterates over sections and for each "modified" file, extracts
    old and new content from the text-based diff, then applies
    block-level structural comparison.

    Sections of type "added", "deleted", "renamed", "moved", or
    "header" are passed through unchanged.

    Args:
        sections: List of DiffSection from watcher.compute_diff().
        fmt: Output format — "markdown" or "xml".

    Returns:
        List of DiffSection with structural diff content replacing
        text-based content for modified files.
    """
    result = []
    for s in sections:
        if s.type != "modified" or not s.path:
            result.append(s)
            continue

        lang = lang_for_path(Path(s.path))
        old_content, new_content = _extract_old_new_from_section(s.content)
        if old_content is not None and new_content is not None:
            structural = structural_diff(old_content, new_content, s.path, lang, fmt)
            if structural.strip():
                s.content = structural

        result.append(s)
    return result


def _extract_old_new_from_section(content: str) -> tuple[str | None, str | None]:
    """Parse a markdown diff section into old and new content.

    Reads REMOVED and ADDED blocks from the diff output, strips
    4-space indentation, and returns the reconstructed old and new
    file contents as separate strings.

    Args:
        content: Markdown diff section content.

    Returns:
        Tuple of (old_content, new_content) or (None, None) if
        the section does not contain extractable content.
    """
    old_lines = []
    new_lines = []
    in_removed = False
    in_added = False

    for line in content.split("\n"):
        if line.startswith("REMOVED "):
            in_removed = True
            in_added = False
            continue
        elif line.startswith("ADDED "):
            in_removed = False
            in_added = True
            continue
        elif (
            line.startswith("### ")
            or line.startswith("[DELETED]")
            or line.startswith("RENAMED")
            or line.startswith("MOVED")
        ):
            in_removed = False
            in_added = False
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


def structural_diff(
    old_content: str,
    new_content: str,
    path: str,
    lang: str,
    fmt: str = "markdown",
) -> str:
    """Compute block-level structural diff between two file versions.

    Dispatches to language-specific parsers based on the detected
    language. Falls back to text-based difflib for unknown languages.

    Args:
        old_content: Original file content (from snapshot).
        new_content: Modified file content (current version).
        path: File path for the diff header.
        lang: Programming language from lang_for_path().
        fmt: Output format — "markdown" or "xml".

    Returns:
        Formatted structural diff string showing MODIFIED, ADDED,
        and DELETED blocks at the function/class level.
    """
    if lang == "python":
        blocks_old = _parse_python_blocks(old_content)
        blocks_new = _parse_python_blocks(new_content)
    elif lang in _C_LIKE_LANGS or lang == "gdscript":
        blocks_old = _parse_c_like_blocks(old_content, lang)
        blocks_new = _parse_c_like_blocks(new_content, lang)
    elif lang in _SCRIPT_LANGS:
        blocks_old = _parse_script_blocks(old_content)
        blocks_new = _parse_script_blocks(new_content)
    else:
        return _fallback_diff(old_content, new_content, path, fmt)

    return _format_block_diff(blocks_old, blocks_new, path, fmt)


# ── Python block parsing (ast) ─────────────────────────────────────


def _parse_python_blocks(text: str) -> dict[str, tuple[str, str]]:
    """Parse Python source into {name: (signature, body)} blocks.

    Uses stdlib ast module. Top-level FunctionDef, ClassDef, and
    AsyncFunctionDef become named blocks. Decorators are preserved
    as part of the signature.

    Args:
        text: Python source code.

    Returns:
        Dict mapping function/class names to (signature, body) tuples.
        Empty dict on SyntaxError.
    """
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


# ── C-like block parsing (regex) ───────────────────────────────────


def _parse_c_like_blocks(text: str, lang: str) -> dict[str, tuple[str, str]]:
    """Parse C-like source into {name: (signature, body)} blocks.

    Uses regex to find function, class, method, and type declarations.
    Bodies are extracted via brace matching for languages that use
    curly braces.

    Args:
        text: Source code in a C-like language.
        lang: Language identifier (unused, reserved for future use).

    Returns:
        Dict mapping block names to (signature, body) tuples.
    """
    sig_pattern = re.compile(
        r"^(\s*(?:export\s+)?(?:async\s+)?(?:function|def|class|interface|enum|struct|trait|impl|"
        r"type\s+\w+\s+\w+|type\s+|"
        r"public\s+class|public\s+static|public\s+function|"
        r"fn|func)\s+(\w+)[^{]*)",
        re.MULTILINE,
    )

    blocks = {}
    for m in sig_pattern.finditer(text):
        name = m.group(2)
        sig = m.group(1).strip()
        body_start = m.end()
        if body_start < len(text) and text[body_start] == "{":
            body = _extract_braced_block(text, body_start)
        else:
            body = ""
        blocks[name] = (sig, body)

    return blocks


def _extract_braced_block(text: str, start: int) -> str:
    """Extract text from an opening brace to its matching closing brace.

    Handles nested braces correctly. Returns the content from '{'
    to the matching '}', inclusive.

    Args:
        text: Full source text.
        start: Index of the opening '{' character.

    Returns:
        Braced block content including the braces, or empty string
        if start is out of range or not pointing to '{'.
    """
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
    """Parse Ruby/Elixir/Lua source into {name: (signature, body)} blocks.

    Uses regex to find def, defmodule, defp, and function declarations.
    Bodies are everything after the signature line.

    Args:
        text: Source code in Ruby, Elixir, or Lua.

    Returns:
        Dict mapping block names to (signature, body) tuples.
    """
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


def _format_block_diff(
    old_blocks: dict[str, tuple[str, str]],
    new_blocks: dict[str, tuple[str, str]],
    path: str,
    fmt: str,
) -> str:
    """Compare two block dicts and produce formatted structural diff.

    Blocks present only in new_blocks are ADDED.
    Blocks present only in old_blocks are DELETED.
    Blocks in both are compared for signature and body changes.

    Args:
        old_blocks: Blocks from the old file version.
        new_blocks: Blocks from the new file version.
        path: File path for the header.
        fmt: Output format — "markdown" or "xml".

    Returns:
        Formatted structural diff string with MODIFIED/ADDED/DELETED
        sections.
    """
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
    """Generate a human-readable label for a code block.

    Detects whether the block is a class or function from its
    signature prefix.

    Args:
        name: Block name (function or class name).
        signature: First line of the block declaration.

    Returns:
        Label like "function calculate_total" or "class ShoppingCart".
    """
    if signature.startswith("class ") or signature.startswith("interface "):
        return f"class {name}"
    elif (
        signature.startswith("def ")
        or signature.startswith("function ")
        or signature.startswith("func ")
    ) or signature.startswith("fn "):
        return f"function {name}"
    else:
        return name


def _fallback_diff(old: str, new: str, path: str, fmt: str) -> str:
    """Fallback to text-based difflib diff for unknown languages.

    Args:
        old: Old file content.
        new: New file content.
        path: File path.
        fmt: Output format.

    Returns:
        Formatted diff string from differ.compute_diff().
    """
    from .differ import compute_diff

    if not old and not new:
        return ""
    return compute_diff(old, new, path, fmt=fmt)
