"""Shared fixtures for all tests."""

import pytest

from arachna.config import load_config


@pytest.fixture(autouse=True)
def _clear_config_cache():
    """Clear load_config LRU cache before each test.

    Tests create .arachna.json dynamically in tmp_path — cached config
    from a previous test's tmp_path would return wrong profiles.
    """
    load_config.cache_clear()
