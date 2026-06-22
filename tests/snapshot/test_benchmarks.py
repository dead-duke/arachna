"""Tests for benchmark functions — structural diff and tiktoken."""

import json

import pytest

from arachna.config.profile_config import ProfileConfig
from arachna.domain.tokenization.tokenizer import _has_tiktoken
from arachna.snapshot.benchmarks import benchmark_structural_diff, benchmark_tiktoken


def _make_profile(**overrides):
    return ProfileConfig(
        name_template="c",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
        **overrides,
    )


class TestBenchmarkStructuralDiff:
    """Tests for benchmark_structural_diff."""

    def test_creates_and_deletes_snapshot(self, tmp_path):
        """Creates snapshot, runs text+structural diff, deletes snapshot."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("def foo():\n    return 1\n")
        (tmp_path / ".arachna.json").write_text(
            json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
        )
        profile = _make_profile()
        result = benchmark_structural_diff(profile, str(tmp_path / "out"), root=tmp_path)
        assert "parts" in result
        assert "tokens" in result
        assert "time" in result
        assert "files" in result
        assert "detail" in result
        assert "create" in result["detail"]
        assert "text_diff" in result["detail"]
        assert "structural_diff" in result["detail"]

    def test_empty_dir(self, tmp_path):
        """Handles empty project directory."""
        (tmp_path / "src").mkdir()
        (tmp_path / ".arachna.json").write_text(
            json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
        )
        profile = _make_profile()
        result = benchmark_structural_diff(profile, str(tmp_path / "out"), root=tmp_path)
        assert result["files"] == 0
        assert result["tokens"] == 0


@pytest.mark.skipif(not _has_tiktoken(), reason="tiktoken not installed")
class TestBenchmarkTiktoken:
    """Tests for benchmark_tiktoken."""

    def test_compares_default_vs_tiktoken(self, tmp_path):
        """Runs full collection with default tokenizer, then tiktoken, compares token counts."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hello world')\n")
        (tmp_path / ".arachna.json").write_text(
            json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
        )
        profile = _make_profile()
        result = benchmark_tiktoken(profile, str(tmp_path / "out"), root=tmp_path)
        assert "parts" in result
        assert "tokens" in result
        assert "files" in result
        assert "detail" in result
        assert "default_tokens" in result["detail"]
        assert "tiktoken_tokens" in result["detail"]
        assert "ratio" in result["detail"]

    def test_empty_dir_zeros(self, tmp_path):
        """Empty project returns zero tokens for both."""
        (tmp_path / "src").mkdir()
        (tmp_path / ".arachna.json").write_text(
            json.dumps({"project_name": "test", "output_dir": "out", "profiles": {}})
        )
        profile = _make_profile()
        result = benchmark_tiktoken(profile, str(tmp_path / "out"), root=tmp_path)
        assert result["tokens"] == 0
        assert result["detail"]["default_tokens"] == 0
        assert result["detail"]["tiktoken_tokens"] == 0
        assert result["detail"]["ratio"] == "0.00x"
