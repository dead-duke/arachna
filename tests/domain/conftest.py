"""Shared fixtures for domain tests."""

from arachna.domain.path_utils import SafePath


def safe_out(tmp_path, name="out"):
    """Create a SafePath output directory for tests."""
    out = tmp_path / name
    out.mkdir(exist_ok=True)
    return SafePath(out, tmp_path)
