# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI command handlers for arachna v4.0.0.

COMMAND_HANDLERS maps argparse command names to handler functions.
Each handler signature: (args: argparse.Namespace, config: dict) -> None.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

COMMAND_HANDLERS: dict[str, Callable[[Any, dict[str, Any]], None]] = {}
"""Registry of CLI command handlers. Populated by cli/*.py modules."""


def register(command: str):
    """Decorator to register a command handler in COMMAND_HANDLERS."""

    def decorator(func: Callable[[Any, dict[str, Any]], None]):
        COMMAND_HANDLERS[command] = func
        return func

    return decorator


# Import all submodules to trigger @register decorators
from . import (  # noqa: E402, F401
    collect,
    completion,
    diff,
    doctor,
    init,
    manifest,
    plugins,
    presets,
    profile,
    snapshot,
    store,
)
