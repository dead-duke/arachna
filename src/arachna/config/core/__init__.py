"""Core config subpackage — config loading, profile resolution, validation."""

from .config import (
    _MAX_EXTENDS_DEPTH,
    _MERGE_APPEND,
    _dict_to_profile,
    _merge_profiles,
    _resolve_profile,
    find_config,
    get_profile,
    load_config,
)
from .validator import (
    validate_profile,
)

__all__ = [
    "_MAX_EXTENDS_DEPTH",
    "_MERGE_APPEND",
    "_dict_to_profile",
    "_merge_profiles",
    "_resolve_profile",
    "find_config",
    "get_profile",
    "load_config",
    "validate_profile",
]
