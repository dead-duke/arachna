"""Presets config subpackage — preset detection, validation, remote fetching."""

from .presets import (
    _SEPARATOR,
    DEFAULT_PRESETS_PATH,
    _detect_any,
    _detect_dir,
    _detect_file,
    _load_builtin_presets,
    _validate_preset,
    detect_presets,
    get_all_presets,
    get_detected_summary,
    load_presets_from_file,
    preset_to_profile,
)
from .presets_remote import (
    fetch_presets,
    merge_presets,
)

__all__ = [
    "DEFAULT_PRESETS_PATH",
    "_SEPARATOR",
    "_detect_any",
    "_detect_dir",
    "_detect_file",
    "_load_builtin_presets",
    "_validate_preset",
    "detect_presets",
    "fetch_presets",
    "get_all_presets",
    "get_detected_summary",
    "load_presets_from_file",
    "merge_presets",
    "preset_to_profile",
]
