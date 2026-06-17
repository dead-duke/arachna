# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Config validator — checks profiles for errors and warnings."""

from pathlib import Path
from typing import Any

from . import VALID_SPLIT_MODES


def _validate_split_mode(profile, errors):
    split_mode = profile.get("split_mode", "by_file")
    if split_mode not in VALID_SPLIT_MODES:
        errors.append(
            f"split_mode: '{split_mode}' is not valid (use: {', '.join(sorted(VALID_SPLIT_MODES))})"
        )


def _validate_max_tokens(profile, errors):
    max_tokens = profile.get("max_tokens", 0)
    if max_tokens < -1 or max_tokens == 0:
        errors.append(f"max_tokens: must be -1 (unlimited) or >= 1, got {max_tokens}")


def _validate_marker(profile, errors):
    if profile.get("split_mode") == "by_marker" and not profile.get("split_marker", ""):
        errors.append("split_marker: required when split_mode is 'by_marker'")


def _validate_content_source(profile, errors):
    if not profile.get("command") and not profile.get("directories") and not profile.get("files"):
        errors.append("No content source: set 'command', 'directories', or 'files'")


def _validate_paths(profile, warnings):
    for d in profile.get("directories", []):
        if not Path(d).exists():
            warnings.append(f"directory not found: {d}")
    for f in profile.get("files", []):
        if not Path(f).exists():
            warnings.append(f"file not found: {f}")


def validate_profile(name: str, profile: dict[str, Any]) -> dict:
    errors = []
    warnings = []
    _validate_split_mode(profile, errors)
    _validate_max_tokens(profile, errors)
    _validate_marker(profile, errors)
    _validate_content_source(profile, errors)
    _validate_paths(profile, warnings)
    return {"name": name, "errors": errors, "warnings": warnings}
