"""Fixtures and baseline management for benchmarks."""


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "benchmark: marks tests as benchmarks (not for CI)")
