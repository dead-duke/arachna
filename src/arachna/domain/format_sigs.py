# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Signature formatting for repo-map mode."""

import json

from .format_headers import _generate_header


def _format_sigs_markdown(filepath, lang, sigs):
    return f"### {filepath}\n\n```{lang if lang else ''}\n{sigs}\n```\n"


def _format_sigs_xml(filepath, lang, sigs):
    lang_attr = f' language="{lang}"' if lang else ""
    return f'<file path="{filepath}"{lang_attr}>\n<![CDATA[\n{sigs}\n]]>\n</file>\n'


def _format_sigs_json(filepath, lang, sigs):
    obj = {"path": str(filepath), "content": sigs}
    if lang:
        obj["language"] = lang
    return json.dumps(obj, ensure_ascii=False) + "\n"


_SIGS_FORMATTERS = {
    "markdown": _format_sigs_markdown,
    "xml": _format_sigs_xml,
    "json": _format_sigs_json,
}


def _apply_repo_map_to_section(filepath, section, raw_text, lang, fmt, include_header, header=""):
    from .splitter import extract_signatures

    if raw_text is None:
        return section
    sigs = extract_signatures(raw_text, lang)
    if not header and include_header:
        header = _generate_header(filepath, raw_text, lang)
    formatter = _SIGS_FORMATTERS.get(fmt, _format_sigs_markdown)
    return header + formatter(filepath, lang, sigs)
