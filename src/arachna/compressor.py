"""Whitespace compression for token savings."""

import re

_RE_BLANK_LINES = re.compile(r"\n{3,}")
_RE_TRAILING_WS = re.compile(r"[ \t]+$", re.MULTILINE)
_RE_INDENT = re.compile(r"^([ \t]+)", re.MULTILINE)


def compress(text: str, indent: bool = False) -> str:
    """Compress whitespace to save tokens.

    - Collapses 3+ blank lines into 2
    - Strips trailing whitespace
    - If indent=True: compresses indentation (8 spaces → 2 spaces)
    """
    text = _RE_BLANK_LINES.sub("\n\n", text)
    text = _RE_TRAILING_WS.sub("", text)

    if indent:

        def _compress_indent(match):
            spaces = match.group(1)
            if "\t" in spaces:
                return "\t"
            return "  "

        text = _RE_INDENT.sub(_compress_indent, text)

    return text


def estimate_savings(original: str, compressed: str) -> tuple[int, int, float]:
    """Return (original_tokens, compressed_tokens, savings_percent)."""
    from .tokenizer import count_tokens

    orig = count_tokens(original)
    comp = count_tokens(compressed)
    pct = ((orig - comp) / orig * 100) if orig > 0 else 0
    return orig, comp, pct
