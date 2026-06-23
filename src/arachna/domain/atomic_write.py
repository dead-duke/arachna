# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Atomic file write with fallback.

Provides atomic write via mkstemp + os.replace with automatic
fallback to direct write when atomic operations fail.
"""

import contextlib
import os
import tempfile

from .path_utils import SafePath


def atomic_write_text(path: SafePath, text: str) -> None:
    """Write text to path atomically using mkstemp + os.replace.

    Creates parent directories if needed.
    Falls back to SafePath.write_text on OSError.
    """
    p = path.to_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd, tmp_path = tempfile.mkstemp(dir=str(p.parent), prefix="." + p.name + "_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp_path, p)
        except (OSError, RuntimeError, ValueError):
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise
    except OSError:
        path.write_text(text, encoding="utf-8")


def atomic_write_bytes(path: SafePath, data: bytes) -> None:
    """Write bytes to path atomically using mkstemp + os.replace.

    Creates parent directories if needed.
    Falls back to SafePath.write_bytes on OSError.
    """
    p = path.to_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd, tmp_path = tempfile.mkstemp(dir=str(p.parent), prefix="." + p.name + "_", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            os.replace(tmp_path, p)
        except (OSError, RuntimeError, ValueError):
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise
    except OSError:
        path.write_bytes(data)
