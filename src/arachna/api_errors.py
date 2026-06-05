"""Public API exceptions for arachna v2.0.0."""


class ArachnaError(Exception):
    """Base exception for all arachna API errors."""


class SnapshotNotFoundError(ArachnaError):
    """Snapshot with the given ID does not exist."""


class SnapshotExistsError(ArachnaError):
    """Snapshot with the given name already exists."""


class ProfileNotFoundError(ArachnaError):
    """Profile with the given name does not exist in .arachna.json."""
