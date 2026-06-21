# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Config validator — checks profiles for errors and warnings."""

from pathlib import Path

from . import VALID_SPLIT_MODES
from .profile_config import ProfileConfig

_DEFAULTS = ProfileConfig()


def _validate_split_mode(profile: ProfileConfig, errors):
    if profile.split_mode not in VALID_SPLIT_MODES:
        errors.append(
            f"split_mode: '{profile.split_mode}' is not valid (use: {', '.join(sorted(VALID_SPLIT_MODES))})"
        )


def _validate_max_tokens(profile: ProfileConfig, errors):
    if profile.max_tokens < -1 or profile.max_tokens == 0:
        errors.append(f"max_tokens: must be -1 (unlimited) or >= 1, got {profile.max_tokens}")


def _validate_marker(profile: ProfileConfig, errors):
    if profile.split_mode == "by_marker" and profile.split_marker == _DEFAULTS.split_marker:
        errors.append("split_marker: required when split_mode is 'by_marker'")


def _validate_content_source(profile: ProfileConfig, errors):
    has_source = (
        profile.command is not None
        or profile.directories != _DEFAULTS.directories
        or profile.files != _DEFAULTS.files
    )
    if not has_source:
        errors.append("No content source: set 'command', 'directories', or 'files'")


def _validate_paths(profile: ProfileConfig, warnings):
    for d in profile.directories:
        if not Path(d).exists():
            warnings.append(f"directory not found: {d}")
    for f in profile.files:
        if not Path(f).exists():
            warnings.append(f"file not found: {f}")


def validate_profile(name: str, profile: ProfileConfig) -> dict:
    errors = []
    warnings = []
    _validate_split_mode(profile, errors)
    _validate_max_tokens(profile, errors)
    _validate_marker(profile, errors)
    _validate_content_source(profile, errors)
    _validate_paths(profile, warnings)
    return {"name": name, "errors": errors, "warnings": warnings}
