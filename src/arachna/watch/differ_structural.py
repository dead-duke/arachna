# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Structural diff — understands code blocks, not just text lines.

For Python: uses ast to parse source into named blocks.
For C-like languages: uses regex to find declarations with brace matching.
For Ruby/Elixir/Lua: regex-based block parsing.
For all other languages: falls back to text-based difflib.

v4.0.1: Block parsers moved to domain/language_dispatch.py.
Uses get_block_parser for language dispatch.
"""

import logging
from pathlib import Path

from ..domain.formatter import C_LIKE_LANGS, lang_for_path
from ..domain.language_dispatch import get_block_parser

logger = logging.getLogger("arachna.differ_structural")

_HAS_TS = False
_HAS_TS_JS = False
_HAS_TS_TS = False
_HAS_TS_GO = False


def _check_plugins():
    global _HAS_TS, _HAS_TS_JS, _HAS_TS_TS, _HAS_TS_GO
    try:
        import tree_sitter  # noqa: F401

        _HAS_TS = True
    except ImportError:
        _HAS_TS = False
        _HAS_TS_JS = False
        _HAS_TS_TS = False
        _HAS_TS_GO = False
        return
    try:
        import tree_sitter_javascript  # noqa: F401

        _HAS_TS_JS = True
    except ImportError:
        _HAS_TS_JS = False
    try:
        import tree_sitter_typescript  # noqa: F401

        _HAS_TS_TS = True
    except ImportError:
        _HAS_TS_TS = False
    try:
        import tree_sitter_go  # noqa: F401

        _HAS_TS_GO = True
    except ImportError:
        _HAS_TS_GO = False


_check_plugins()


def _has_tree_sitter_for(lang: str) -> bool:
    if lang == "javascript":
        return _HAS_TS_JS
    elif lang in ("typescript", "tsx"):
        return _HAS_TS_TS
    elif lang == "go":
        return _HAS_TS_GO
    return False


def structural_diff_sections(sections: list, fmt: str = "markdown") -> list:
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


def structural_diff_for_lang(old_content, new_content, path, lang, fmt="markdown"):
    if _has_tree_sitter_for(lang):
        return _structural_diff_tree_sitter(old_content, new_content, path, lang, fmt)

    if lang in C_LIKE_LANGS and not _has_tree_sitter_for(lang):
        logger.warning(
            "Tree-sitter plugin not installed for %s. "
            "Install: pip install arachna[%s]. Using regex fallback (may be inaccurate).",
            lang,
            lang,
        )

    parser = get_block_parser(lang)
    if parser is None:
        return _fallback_diff(old_content, new_content, path, fmt)

    if lang in C_LIKE_LANGS or lang == "gdscript":
        blocks_old = parser(old_content, lang)
        blocks_new = parser(new_content, lang)
    else:
        blocks_old = parser(old_content)
        blocks_new = parser(new_content)

    if blocks_old is None or blocks_new is None:
        return _fallback_diff(old_content, new_content, path, fmt)

    return _format_block_diff(blocks_old, blocks_new, path, fmt)


def _structural_diff_tree_sitter(old_content, new_content, path, lang, fmt):
    try:
        import tree_sitter

        if lang == "javascript":
            import tree_sitter_javascript as ts_lang
        elif lang in ("typescript", "tsx"):
            import tree_sitter_typescript as ts_lang
        elif lang == "go":
            import tree_sitter_go as ts_lang
        else:
            return _fallback_diff(old_content, new_content, path, fmt)

        ts_language = tree_sitter.Language(ts_lang.language())
        parser_obj = tree_sitter.Parser(ts_language)

        old_tree = parser_obj.parse(old_content.encode("utf-8"))
        new_tree = parser_obj.parse(new_content.encode("utf-8"))

        old_blocks = {}
        _extract_ts_blocks(old_tree.root_node, old_content, old_blocks, lang)
        new_blocks = {}
        _extract_ts_blocks(new_tree.root_node, new_content, new_blocks, lang)

        return _format_block_diff(old_blocks, new_blocks, path, fmt)
    except ImportError:
        return _fallback_diff(old_content, new_content, path, fmt)
    except Exception as e:
        logger.warning("Tree-sitter diff failed for %s: %s. Falling back to text diff.", path, e)
        return _fallback_diff(old_content, new_content, path, fmt)


def _extract_ts_blocks(node, text, blocks, lang):
    func_types = {"function_declaration", "method_definition", "arrow_function"}
    class_types = {"class_declaration"}
    if lang == "go":
        func_types = {"function_declaration", "method_declaration"}
        class_types = {"type_declaration"}

    if node.type in func_types or node.type in class_types:
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            name = text[name_node.start_byte : name_node.end_byte]
            body_node = node.child_by_field_name("body")
            if body_node is not None:
                body_start = body_node.start_byte
                body = text[body_start : body_node.end_byte]
                sig = text[node.start_byte : body_start]
            else:
                body = ""
                sig = text[node.start_byte : node.end_byte]
            blocks[name] = (sig.strip(), body.strip())

    for child in node.children:
        _extract_ts_blocks(child, text, blocks, lang)


def structural_diff(old_content, new_content, path, lang, fmt="markdown"):
    return structural_diff_for_lang(old_content, new_content, path, lang, fmt)


def _extract_old_new_from_section(content):
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


def _format_block_diff(old_blocks, new_blocks, path, fmt):
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


def _block_label(name, signature):
    if signature.startswith(("class ", "interface ")):
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


def _fallback_diff(old, new, path, fmt):
    from .differ import compute_diff as differ_compute_diff

    if not old and not new:
        return ""
    return differ_compute_diff(old, new, path, fmt=fmt)
