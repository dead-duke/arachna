"""Split content into token-limited parts."""

from collections.abc import Callable

from .tokenizer import count_tokens

# Conservative estimate: 4 characters ≈ 1 token
CHARS_PER_TOKEN = 4


def split(
    raw_content: str,
    max_tokens: int,
    mode: str = "by_file",
    marker: str = "\n\n",
    separator: str = "\n\n",
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    tk = tokenizer if tokenizer is not None else count_tokens

    if mode == "by_file":
        sections = _split_to_sections(raw_content, "\n\n### ")
    elif mode == "by_paragraph":
        sections = _split_to_sections(raw_content, "\n\n")
    elif mode == "by_marker":
        sections = _split_to_sections(raw_content, marker)
    elif mode == "single":
        parts, was_truncated = _handle_single(raw_content, max_tokens, tokenizer=tk)
        if was_truncated:
            print(
                f"  Warning: content is {tk(raw_content)} tokens, "
                f"limit {max_tokens} — truncating"
            )
        return parts
    else:
        sections = _split_to_sections(raw_content, "\n\n### ")

    return _build_parts(sections, max_tokens, separator=separator, tokenizer=tk)


def _split_to_sections(text: str, marker: str) -> list[str]:
    chunks = text.split(marker)
    result = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            if chunk.strip():
                result.append(chunk.strip())
        else:
            result.append(marker + chunk)
    return result


def _build_parts(
    sections: list[str],
    max_tokens: int,
    separator: str = "\n\n",
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    tk = tokenizer if tokenizer is not None else count_tokens

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
            print(
                f"  Warning: section too large ({section_tokens} tokens, limit {max_tokens}), writing as-is"
            )
            parts.append(section)
            continue

        if current_tokens + section_tokens > max_tokens:
            parts.append(current.strip())
            current = section
            current_tokens = section_tokens
        else:
            if current:
                current += separator + section
            else:
                current = section
            current_tokens += section_tokens

    if current.strip():
        parts.append(current.strip())

    return parts


def _handle_single(
    text: str,
    max_tokens: int,
    tokenizer: Callable[[str], int] | None = None,
) -> tuple[list[str], bool]:
    """Split content into a single part, truncating if over limit.

    Returns (parts, was_truncated).
    """
    tk = tokenizer if tokenizer is not None else count_tokens

    tokens = tk(text)
    if tokens > max_tokens:
        max_chars = max_tokens * CHARS_PER_TOKEN
        text = text[:max_chars] + "\n\n# ... truncated ...\n"
        return [text.strip()], True
    return [text.strip()], False
