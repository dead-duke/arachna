# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Config validator — checks profiles for errors and warnings."""

from pathlib import Path
from typing import Any

from . import VALID_SPLIT_MODES


def validate_profile(name: str, profile: dict[str, Any]) -> dict:
    """Validate a single profile.

    Returns dict with:
        name: profile name
        errors: list of error messages
        warnings: list of warning messages
    """
    errors = []
    warnings = []

    split_mode = profile.get("split_mode", "by_file")
    if split_mode not in VALID_SPLIT_MODES:
        errors.append(
            f"split_mode: '{split_mode}' is not valid (use: {', '.join(sorted(VALID_SPLIT_MODES))})"
        )

    max_tokens = profile.get("max_tokens", 0)
    if max_tokens < -1 or max_tokens == 0:
        errors.append(f"max_tokens: must be -1 (unlimited) or >= 1, got {max_tokens}")

    if split_mode == "by_marker":
        marker = profile.get("split_marker", "")
        if not marker:
            errors.append("split_marker: required when split_mode is 'by_marker'")

    has_command = bool(profile.get("command"))
    has_dirs = bool(profile.get("directories"))
    has_files = bool(profile.get("files"))
    if not has_command and not has_dirs and not has_files:
        errors.append("No content source: set 'command', 'directories', or 'files'")

    for d in profile.get("directories", []):
        if not Path(d).exists():
            warnings.append(f"directory not found: {d}")

    for f in profile.get("files", []):
        if not Path(f).exists():
            warnings.append(f"file not found: {f}")

    return {
        "name": name,
        "errors": errors,
        "warnings": warnings,
    }
