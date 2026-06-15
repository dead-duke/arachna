# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Protocol interfaces for core abstractions in arachna v4.0.0.

These typing.Protocol classes formalize the duck-typed interfaces
used throughout the codebase. They serve as documentation and enable
static type checking without introducing runtime dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class Tokenizer(Protocol):
    """Callable that estimates token count for a string.

    Minimal contract: given text, return estimated token count.
    """

    def __call__(self, text: str) -> int: ...


class ObjectStore(Protocol):
    """Content-addressable store for Watch snapshots.

    Minimal contract for store operations used by watcher and diff.
    """

    def write_object(self, data: bytes) -> str: ...
    def read_object(self, object_hash: str) -> bytes: ...
    def create_snapshot(self, files: dict[str, str], name: str | None = None) -> str: ...
    def load_snapshot(self, snapshot_id: str) -> dict: ...
    def list_snapshots(self) -> list[dict]: ...
    def delete_snapshot(self, snapshot_id: str) -> None: ...


class ContentFormatter(Protocol):
    """Formats a file for AI consumption.

    Minimal contract: given a path, return formatted content string.
    Callers don't need to know about binary/include_binary/etc.
    """

    def __call__(self, path: Path) -> str: ...
