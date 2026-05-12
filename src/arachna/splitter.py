"""Split content into token-limited parts."""

from .tokenizer import count_tokens


def split(
    raw_content: str,
    max_tokens: int,
    mode: str = "by_file",
    marker: str = "\n\n",
    separator: str = "\n\n",
) -> list[str]:
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

    return _build_parts(sections, max_tokens, separator)


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


def _build_parts(sections: list[str], max_tokens: int, separator: str = "\n\n") -> list[str]:
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
                current += separator + section
            else:
                current = section
            current_tokens += section_tokens

    if current.strip():
        parts.append(current.strip())

    return parts


def _handle_single(text: str, max_tokens: int) -> list[str]:
    tokens = count_tokens(text)
    if tokens > max_tokens:
        print(f"  Warning: content is {tokens} tokens, limit {max_tokens} — truncating")
        max_chars = max_tokens * 4
        text = text[:max_chars] + "\n\n# ... truncated ...\n"
    return [text.strip()]
