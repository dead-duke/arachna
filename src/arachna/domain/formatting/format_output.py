"""File formatting for markdown/xml/json output."""

import json
import os as _os

from ...config import OutputFormat
from ..path_utils import SafePath
from .format_binary import (
    _format_binary,
    _format_binary_for_fmt,
    _is_binary_allowed,
    _should_skip_binary,
    _skip_reason_label,
)
from .format_headers import _generate_header
from .format_language import _lang_from_shebang, lang_for_path

_ARACHNA_MAX_FILE_SIZE = int(_os.environ.get("ARACHNA_MAX_FILE_SIZE", 100 * 1024 * 1024))


def _add_line_numbers(text: str) -> str:
    if not text:
        return text
    lines = text.split("\n")
    width = max(5, len(str(len(lines))))
    return "\n".join(f"{i:>{width}}| {line}" for i, line in enumerate(lines, 1))


def _try_read_text(path):
    try:
        return ("text", path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return ("unicode_error", None)
    except PermissionError:
        return ("permission_error", None)
    except OSError as e:
        return ("os_error", e)


def _handle_unicode_error(path, include_binary, binary_extensions, binary_max_mb, verbose):
    if include_binary and _is_binary_allowed(path, binary_extensions, binary_max_mb):
        return ("binary", _format_binary(path, "markdown"))
    if verbose:
        print(f"  Skipped (binary): {path}")
    return ("skip", "")


def _handle_verbose_skip(status, path, detail, verbose):
    if verbose:
        if status == "permission_error":
            print(f"  Skipped (permission): {path}")
        elif status == "os_error":
            print(f"  Skipped (error): {path} - {detail}")
    return ("skip", "")


def _handle_read_error(
    status, detail, path, include_binary, binary_extensions, binary_max_mb, verbose
):
    if status == "unicode_error":
        return _handle_unicode_error(
            path, include_binary, binary_extensions, binary_max_mb, verbose
        )
    return _handle_verbose_skip(status, path, detail, verbose)


def _read_text_content(path, include_binary, binary_extensions, binary_max_mb, verbose):
    status, content = _try_read_text(path)
    if status != "text":
        return _handle_read_error(
            status, content, path, include_binary, binary_extensions, binary_max_mb, verbose
        )
    if "\x00" in content:
        if include_binary and _is_binary_allowed(path, binary_extensions, binary_max_mb):
            return ("binary", _format_binary(path, "markdown"))
        if verbose:
            print(f"  Skipped (binary): {path}")
        return ("skip", "")
    return ("text", content)


def _resolve_lang(path, text):
    lang = lang_for_path(path)
    if not lang and text:
        lang = _lang_from_shebang(text.split("\n")[0])
    return lang


def _format_markdown(path, lang, text):
    return f"### {path}\n\n```{lang}\n{text}\n```\n"


def _format_xml(path, lang, text):
    lang_attr = f' language="{lang}"' if lang else ""
    return f'<file path="{path}"{lang_attr}>\n<![CDATA[\n{text}\n]]>\n</file>\n'


def _format_json(path, lang, text):
    obj = {"path": str(path), "content": text}
    if lang:
        obj["language"] = lang
    return json.dumps(obj, ensure_ascii=False) + "\n"


def _format_content(path, text, fmt, include_header, line_numbers):
    if line_numbers:
        text = _add_line_numbers(text)
    lang = _resolve_lang(path, text)
    header = _generate_header(path, text, lang) if include_header else ""
    if fmt == "xml":
        return header + _format_xml(path, lang, text)
    elif fmt == "json":
        return header + _format_json(path, lang, text)
    return header + _format_markdown(path, lang, text)


def _format_valid_file(
    path,
    fmt,
    include_binary,
    binary_extensions,
    binary_max_mb,
    verbose,
    include_header,
    line_numbers,
):
    try:
        st_size = path.stat().st_size
    except OSError as e:
        if verbose:
            print(f"  Skipped (error): {path} - {e}")
        return ""
    if st_size > _ARACHNA_MAX_FILE_SIZE:
        if verbose:
            size_mb = st_size / (1024 * 1024)
            limit_mb = _ARACHNA_MAX_FILE_SIZE / (1024 * 1024)
            print(f"  Skipped (file too large: {size_mb:.1f}MB > {limit_mb:.0f}MB): {path}")
        return ""
    status, content = _read_text_content(
        path, include_binary, binary_extensions, binary_max_mb, verbose
    )
    if status == "skip":
        return ""
    if status == "binary":
        return _format_binary_for_fmt(content, path, fmt)
    return _format_content(path, content, fmt, include_header, line_numbers)


def format_file_section(
    path,
    fmt: OutputFormat = "markdown",
    include_binary=False,
    binary_extensions=None,
    binary_max_mb=1.0,
    verbose=False,
    include_header=False,
    line_numbers=False,
    root=None,
):
    if root is not None:
        try:
            path = SafePath(path, root)
        except ValueError:
            if verbose:
                print(f"  Skipped (path traversal): {path}")
            return ""
    if _should_skip_binary(path, include_binary, binary_extensions, binary_max_mb):
        if verbose:
            try:
                path.stat()
            except OSError as e:
                print(f"  Skipped (error): {path} - {e}")
                return ""
            reason = _skip_reason_label(path, include_binary, binary_extensions, binary_max_mb)
            print(f"  Skipped ({reason}): {path}")
        return ""
    return _format_valid_file(
        path,
        fmt,
        include_binary,
        binary_extensions,
        binary_max_mb,
        verbose,
        include_header,
        line_numbers,
    )
