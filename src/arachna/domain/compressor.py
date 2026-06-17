# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Whitespace compression for token savings."""


def compress(text: str) -> str:
    """Compress whitespace to save tokens.

    - Collapses 3+ blank lines into 2
    - Strips trailing whitespace

    Safe for all code and markup - does not modify indentation.
    """
    result = []
    newline_count = 0
    for ch in text:
        if ch == "\n":
            newline_count += 1
        else:
            if newline_count > 0:
                result.append("\n" * min(newline_count, 2))
                newline_count = 0
            result.append(ch)
    if newline_count > 0:
        result.append("\n" * min(newline_count, 2))
    text = "".join(result)
    text = "\n".join(line.rstrip(" \t") for line in text.split("\n"))
    return text


def estimate_savings(original: str, compressed: str) -> tuple[int, int, float]:
    """Return (original_tokens, compressed_tokens, savings_percent)."""
    from .tokenizer import count_tokens

    orig = count_tokens(original)
    comp = count_tokens(compressed)
    pct = ((orig - comp) / orig * 100) if orig > 0 else 0
    return orig, comp, pct
