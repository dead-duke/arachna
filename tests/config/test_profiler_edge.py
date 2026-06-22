"""Tests for profiler — JSON output, empty query candidate."""

import json
from io import StringIO

from arachna.config.profile_config import ProfileConfig
from arachna.config.profiler import _find_query_candidate, print_benchmark_table


def test_print_benchmark_table_json():
    """JSON format outputs valid JSON with all keys."""
    results = {
        "full": {"parts": 1, "tokens": 500, "time": 0.1, "files": 5},
        "repo-map": {"parts": 1, "tokens": 200, "time": 0.05, "files": 3},
    }
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    print_benchmark_table(results, fmt="json")
    sys.stdout = old
    data = json.loads(out.getvalue())
    assert "full" in data
    assert data["full"]["tokens"] == 500


def test_print_benchmark_table_empty():
    """Empty results prints nothing."""
    out = StringIO()
    import sys

    old = sys.stdout
    sys.stdout = out
    print_benchmark_table({}, fmt="terminal")
    sys.stdout = old
    assert "No benchmark results" in out.getvalue()


def test_find_query_candidate_no_files(tmp_path):
    """Returns None when no matching files found."""
    (tmp_path / "empty").mkdir()
    profile = ProfileConfig(
        directories=["empty"],
        patterns=["*.py"],
        exclude_patterns=[],
    )
    result = _find_query_candidate(profile, root=tmp_path)
    assert result is None
