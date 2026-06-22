# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Protocol interfaces for core abstractions.

These typing.Protocol classes formalize the duck-typed interfaces
used throughout the codebase. They serve as documentation and enable
static type checking without introducing runtime dependencies.
"""

from __future__ import annotations

from typing import Protocol


class Tokenizer(Protocol):
    """Callable that estimates token count for a string.

    Minimal contract: given text, return estimated token count.
    """

    def __call__(self, text: str) -> int: ...
