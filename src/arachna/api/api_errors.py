# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Public API exceptions for arachna v4.0.0.

All exceptions inherit from ArachnaError for easy catching.
Specific exceptions carry the relevant identifier in the message.
"""


class ArachnaError(Exception):
    """Base exception for all arachna API errors."""


class SnapshotNotFoundError(ArachnaError):
    """Raised when a snapshot with the given ID does not exist."""


class SnapshotExistsError(ArachnaError):
    """Raised when trying to create a snapshot with a duplicate name."""


class ProfileNotFoundError(ArachnaError):
    """Raised when a profile name is not found in .arachna.json."""
