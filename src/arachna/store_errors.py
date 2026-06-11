# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Exceptions for the Watch store subsystem."""


class StoreError(Exception):
    """Base exception for store errors."""


class CorruptedStoreError(StoreError):
    """Object content doesn't match its SHA256 hash."""


class ObjectNotFoundError(StoreError):
    """Object not found in the store."""


class SnapshotExistsError(StoreError):
    """Snapshot with this name already exists."""
