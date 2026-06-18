"""Shared fixtures for domain tests — re-exports from tests/conftest.py."""

from unittest.mock import MagicMock


def mock_popen(stdout=""):
    """Create a mock subprocess.Popen that returns given stdout."""
    mock = MagicMock()
    mock.stdout.read.side_effect = [stdout, ""]
    mock.wait.return_value = 0
    return mock
