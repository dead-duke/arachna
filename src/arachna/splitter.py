"""Split content into token-limited parts."""

from .tokenizer import count_tokens


def split(
    raw_content: str,
    max_tokens: int,
    mode: str = "by_file",
    marker: str = "\n\n",
) -> list[str]:
    """Split raw content into token-limited parts using given mode.

    Modes:
        by_file — atomic file sections (### prefix), never split inside a file
        by_paragraph — split by double newlines
        by_marker — split by custom marker string
        single — no split, truncate if exceeds limit
    """
    if mode == "by_file":
        sections = _split_to_sections(raw_content, "\n\n### ")
    elif mode == "by_paragraph":
        sections = _split_to_sections(raw_content, "\n\n")
    elif mode == "by_marker":
        sections = _split_to_sections(raw_content, marker)
    elif mode == "single":
        return _handle_single(raw_content, max_tokens)
    else:
        sections = _split_to_sections(raw_content, "\n\n### ")

    return _build_parts(sections, max_tokens)


def _split_to_sections(text: str, marker: str) -> list[str]:
    """Split text by marker, restoring marker on all chunks except the first."""
    chunks = text.split(marker)
    result = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            if chunk.strip():
                result.append(chunk.strip())
        else:
            result.append(marker + chunk)
    return result


def _build_parts(sections: list[str], max_tokens: int) -> list[str]:
    """Build parts from atomic sections, never splitting inside a section."""
    parts = []
    current = ""
    current_tokens = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue
        section_tokens = count_tokens(section)

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
                current += "\n\n" + section
            else:
                current = section
            current_tokens += section_tokens

    if current.strip():
        parts.append(current.strip())

    return parts


def _handle_single(text: str, max_tokens: int) -> list[str]:
    """Single mode — no split, truncate if needed."""
    tokens = count_tokens(text)
    if tokens > max_tokens:
        print(f"  Warning: content is {tokens} tokens, limit {max_tokens} — truncating")
        max_chars = max_tokens * 4
        text = text[:max_chars] + "\n\n# ... truncated ...\n"
    return [text.strip()]
