# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Atomic file write with fallback.

Provides atomic write via mkstemp + os.replace with automatic
fallback to direct write when atomic operations fail.
"""

import contextlib
import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, text: str) -> None:
    """Write text to path atomically using mkstemp + os.replace.

    Creates parent directories if needed.
    Falls back to Path.write_text on OSError.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent), prefix="." + path.name + "_", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp_path, path)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise
    except OSError:
        path.write_text(text, encoding="utf-8")


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write bytes to path atomically using mkstemp + os.replace.

    Creates parent directories if needed.
    Falls back to Path.write_bytes on OSError.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent), prefix="." + path.name + "_", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            os.replace(tmp_path, path)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise
    except OSError:
        path.write_bytes(data)
