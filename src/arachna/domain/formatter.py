# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""File formatting for markdown output — re-exports from sub-modules.

This module is the public API for formatting. All implementation lives in:
- format_language.py — language detection, C_LIKE_LANGS, SCRIPT_LANGS
- format_binary.py — binary detection, base64 encoding
- format_headers.py — deps/exports extraction
- format_output.py — file section formatting (markdown/xml/json)
- format_exclude.py — exclusion pattern matching
- format_sigs.py — signature formatting for repo-map mode
"""

from .format_binary import (
    _format_binary,
    _format_binary_for_fmt,
    _is_binary_allowed,
    _should_skip_binary,
    _skip_reason_label,
)
from .format_exclude import _match_directory_pattern, is_excluded
from .format_headers import (
    _C_LIKE_IMPORT_PATTERNS,
    _generate_header,
    _parse_c_like,
    _parse_import_stmt,
    _parse_multiline_import,
    _parse_python,
    _parse_python_ast,
    _parse_python_imports_fallback,
    _parse_script,
    _parse_script_deps,
    _parse_script_exports,
)
from .format_language import (
    _EXT_LANG,
    _FILENAME_LANG,
    _SHEBANG_MAP,
    _TEXT_EXTENSIONS,
    C_LIKE_LANGS,
    SCRIPT_LANGS,
    _lang_from_shebang,
    lang_for_path,
)
from .format_output import (
    _add_line_numbers,
    _format_content,
    _format_json,
    _format_markdown,
    _format_valid_file,
    _format_xml,
    _handle_read_error,
    _handle_unicode_error,
    _handle_verbose_skip,
    _read_text_content,
    _resolve_lang,
    _try_read_text,
    format_file_section,
)
from .format_sigs import (
    _SIGS_FORMATTERS,
    _apply_repo_map_to_section,
    _format_sigs_json,
    _format_sigs_markdown,
    _format_sigs_xml,
)

__all__ = [
    # format_binary
    "_format_binary",
    "_format_binary_for_fmt",
    "_is_binary_allowed",
    "_should_skip_binary",
    "_skip_reason_label",
    # format_exclude
    "_match_directory_pattern",
    "is_excluded",
    # format_headers
    "_C_LIKE_IMPORT_PATTERNS",
    "_generate_header",
    "_parse_c_like",
    "_parse_import_stmt",
    "_parse_multiline_import",
    "_parse_python",
    "_parse_python_ast",
    "_parse_python_imports_fallback",
    "_parse_script",
    "_parse_script_deps",
    "_parse_script_exports",
    # format_language
    "C_LIKE_LANGS",
    "SCRIPT_LANGS",
    "_EXT_LANG",
    "_FILENAME_LANG",
    "_SHEBANG_MAP",
    "_TEXT_EXTENSIONS",
    "_lang_from_shebang",
    "lang_for_path",
    # format_output
    "_add_line_numbers",
    "_format_content",
    "_format_json",
    "_format_markdown",
    "_format_valid_file",
    "_format_xml",
    "_handle_read_error",
    "_handle_unicode_error",
    "_handle_verbose_skip",
    "_read_text_content",
    "_resolve_lang",
    "_try_read_text",
    "format_file_section",
    # format_sigs
    "_SIGS_FORMATTERS",
    "_apply_repo_map_to_section",
    "_format_sigs_json",
    "_format_sigs_markdown",
    "_format_sigs_xml",
]
