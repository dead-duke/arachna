"""Shared fixtures for all tests."""

import pytest

from arachna.config import find_config


@pytest.fixture(autouse=True)
def _clear_find_config_cache():
    """Clear find_config LRU cache before each test.

    Each test runs in its own tmp_path with its own .arachna.json.
    Cached result from previous test would return wrong path.
    """
    find_config.cache_clear()
