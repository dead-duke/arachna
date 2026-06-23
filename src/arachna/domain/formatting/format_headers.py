"""File header generation — deps and exports extraction for all languages."""

from pathlib import Path

from .format_parsers import (
    get_header_parser,
)


def _generate_header(path: Path, text: str, lang: str) -> str:
    parser = get_header_parser(lang)
    if parser is None:
        return ""
    deps, exports = parser(text)
    if not deps and not exports:
        return ""
    lines = [f"### {path}\n"]
    if deps:
        lines.append(f"deps: {', '.join(sorted(set(deps)))}\n")
    if exports:
        lines.append(f"exports: {', '.join(sorted(set(exports)))}\n")
    return "".join(lines)
