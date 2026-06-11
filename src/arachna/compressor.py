# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Whitespace compression for token savings."""

import re

_RE_BLANK_LINES = re.compile(r"\n{3,}")
_RE_TRAILING_WS = re.compile(r"[ \t]+$", re.MULTILINE)


def compress(text: str) -> str:
    """Compress whitespace to save tokens.

    - Collapses 3+ blank lines into 2
    - Strips trailing whitespace

    Safe for all code and markup — does not modify indentation.
    """
    text = _RE_BLANK_LINES.sub("\n\n", text)
    text = _RE_TRAILING_WS.sub("", text)
    return text


def estimate_savings(original: str, compressed: str) -> tuple[int, int, float]:
    """Return (original_tokens, compressed_tokens, savings_percent)."""
    from .tokenizer import count_tokens

    orig = count_tokens(original)
    comp = count_tokens(compressed)
    pct = ((orig - comp) / orig * 100) if orig > 0 else 0
    return orig, comp, pct
