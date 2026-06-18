"""Tests for validate_snapshot_id in store.py (v2.9.0)."""

import pytest

from arachna.snapshot.store import validate_snapshot_id


def test_valid_snapshot_ids():
    validate_snapshot_id("cycle")
    validate_snapshot_id("my-snap")
    validate_snapshot_id("v1.2.3")
    validate_snapshot_id("snap_2024")
    validate_snapshot_id("test-123.v2")


def test_empty_id_rejected():
    with pytest.raises(ValueError, match="Invalid snapshot ID"):
        validate_snapshot_id("")


def test_path_traversal_rejected():
    with pytest.raises(ValueError, match="Invalid snapshot ID"):
        validate_snapshot_id("../../etc/passwd")
    with pytest.raises(ValueError, match="Invalid snapshot ID"):
        validate_snapshot_id("../outside")
    with pytest.raises(ValueError, match="Invalid snapshot ID"):
        validate_snapshot_id("snap/../etc")


def test_special_chars_rejected():
    with pytest.raises(ValueError, match="Invalid snapshot ID"):
        validate_snapshot_id("snap; rm -rf /")
    with pytest.raises(ValueError, match="Invalid snapshot ID"):
        validate_snapshot_id("snap|cat")
    with pytest.raises(ValueError, match="Invalid snapshot ID"):
        validate_snapshot_id("snap&whoami")


def test_leading_dot_rejected():
    with pytest.raises(ValueError, match="Invalid snapshot ID"):
        validate_snapshot_id(".hidden")


def test_leading_hyphen_rejected():
    with pytest.raises(ValueError, match="Invalid snapshot ID"):
        validate_snapshot_id("-bad")
