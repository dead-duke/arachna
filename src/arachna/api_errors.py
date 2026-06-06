"""Public API exceptions for arachna v2.0.0.

All exceptions inherit from ArachnaError for easy catching.
Specific exceptions carry the relevant identifier in the message.

Usage:
    from arachna.api_errors import (
        ArachnaError,
        SnapshotNotFoundError,
        SnapshotExistsError,
        ProfileNotFoundError,
    )

    try:
        watch.create_snapshot(profile="full", name="my-snap")
    except SnapshotExistsError:
        watch.update_snapshot("my-snap")
    except ProfileNotFoundError:
        print("Profile 'full' not found in .arachna.json")
    except ArachnaError as e:
        print(f"Unexpected error: {e}")
"""


class ArachnaError(Exception):
    """Base exception for all arachna API errors.

    Catch this to handle any arachna-specific error.
    """


class SnapshotNotFoundError(ArachnaError):
    """Raised when a snapshot with the given ID does not exist.

    This can occur when:
    - Calling snapshot_info() with a non-existent ID.
    - Calling delete_snapshot() on an already-deleted snapshot.
    - Calling update_snapshot() on a non-existent snapshot.
    - Calling compute_diff() when no snapshots exist at all.
    """


class SnapshotExistsError(ArachnaError):
    """Raised when trying to create a snapshot with a duplicate name.

    Use update_snapshot() to refresh an existing snapshot,
    or delete_snapshot() first to replace it.
    """


class ProfileNotFoundError(ArachnaError):
    """Raised when a profile name is not found in .arachna.json.

    This can occur when:
    - Passing an unknown profile name to create_snapshot().
    - Passing an unknown profile name to compute_diff().
    - Passing an unknown profile name to collect().
    """
