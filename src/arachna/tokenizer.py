"""Token estimation for local AI models.

Conservative estimate: 4 characters ≈ 1 token.
Works without external dependencies — only Python stdlib.
"""


def count_tokens(text: str) -> int:
    """Return conservative token count for text.

    Most models use ~2-6 characters per token.
    Using 4 gives safe margin for context limits.
    """
    return max(1, len(text) // 4)
