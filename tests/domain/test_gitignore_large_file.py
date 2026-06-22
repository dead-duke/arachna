"""Tests for gitignore large file skipping."""

from arachna.domain.execution.gitignore import _should_skip_gitignore


def test_should_skip_large_gitignore(tmp_path):
    """Gitignore exceeding 100KB is skipped."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n" * 20000)
    assert _should_skip_gitignore(gitignore, tmp_path)
