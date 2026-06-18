# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Binary file detection and base64 formatting."""

import base64
import json
from pathlib import Path

from .format_language import _TEXT_EXTENSIONS


def _skip_reason_label(path, include_binary, binary_extensions, binary_max_mb):
    try:
        size_mb = path.stat().st_size / (1024 * 1024)
    except OSError:
        return "binary"
    ext = path.suffix.lower()
    if size_mb > binary_max_mb:
        return "binary too large"
    if not include_binary:
        return "binary"
    if binary_extensions is not None and ext not in binary_extensions:
        return "binary not in allowlist"
    return "binary"


def _should_skip_binary(path, include_binary, binary_extensions, binary_max_mb):
    ext = path.suffix.lower()
    if ext in _TEXT_EXTENSIONS:
        return False
    try:
        size_mb = path.stat().st_size / (1024 * 1024)
    except OSError:
        return True
    if size_mb > binary_max_mb:
        return True
    if binary_extensions is not None:
        return ext not in binary_extensions
    if not include_binary:
        try:
            with open(path, "rb") as f:
                return b"\x00" in f.read(1024)
        except OSError:
            return True
    return not include_binary


def _is_binary_allowed(path, extensions, max_mb):
    if extensions is not None and path.suffix.lower() not in extensions:
        return False
    try:
        return path.stat().st_size / (1024 * 1024) <= max_mb
    except OSError:
        return False


def _format_binary(path, fmt):
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    ext = path.suffix.lstrip(".").lower()
    if fmt == "xml":
        return f'<file path="{path}" encoding="base64" extension="{ext}">\n{b64}\n</file>\n'
    elif fmt == "json":
        return (
            json.dumps(
                {"path": str(path), "encoding": "base64", "content": b64}, ensure_ascii=False
            )
            + "\n"
        )
    else:
        return f"### {path}\n\n```base64\n{b64}\n```\n"


def _format_binary_for_fmt(binary_content, path, fmt):
    if fmt in ("xml", "json"):
        data = Path(path).read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        ext = Path(path).suffix.lstrip(".").lower()
        if fmt == "xml":
            return f'<file path="{path}" encoding="base64" extension="{ext}">\n{b64}\n</file>\n'
        else:
            return (
                json.dumps(
                    {"path": str(path), "encoding": "base64", "content": b64}, ensure_ascii=False
                )
                + "\n"
            )
    return binary_content
