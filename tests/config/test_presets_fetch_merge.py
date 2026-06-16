"""Tests for fetch_presets and merge_presets in presets.py (v2.4.0)."""

import json
from unittest.mock import MagicMock, patch

from arachna.config.presets import _load_builtin_presets, fetch_presets, merge_presets


def _mock_urlopen(response_bytes):
    """Create a mock that returns response_bytes from read()."""
    mock = MagicMock()
    mock.read.return_value = response_bytes
    return mock


def test_fetch_presets_success():
    """fetch_presets downloads and parses valid JSON from URL."""
    mock_response = json.dumps(
        {
            "python": {
                "dirs": ["src"],
                "patterns": ["*.py"],
                "max_tokens": 32000,
                "split_mode": "by_file",
                "detect": ["src"],
            },
            "go": {
                "dirs": ["."],
                "patterns": ["*.go"],
                "files": ["go.mod"],
                "max_tokens": 16000,
                "split_mode": "by_file",
                "detect": ["go.mod"],
            },
        }
    ).encode("utf-8")

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(mock_response)):
        result = fetch_presets("https://example.com/presets.json")

    assert "python" in result
    assert "go" in result
    assert result["python"]["max_tokens"] == 32000
    assert result["go"]["patterns"] == ["*.go"]


def test_fetch_presets_network_error():
    """fetch_presets returns empty dict on network error."""
    with patch("urllib.request.urlopen", side_effect=OSError("Network unreachable")):
        result = fetch_presets("https://example.com/presets.json")
    assert result == {}


def test_fetch_presets_invalid_json():
    """fetch_presets returns empty dict on invalid JSON."""
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(b"not json")):
        result = fetch_presets("https://example.com/presets.json")
    assert result == {}


def test_fetch_presets_not_object():
    """fetch_presets returns empty dict when root is not an object."""
    mock_response = json.dumps(["list", "not", "object"]).encode("utf-8")
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(mock_response)):
        result = fetch_presets("https://example.com/presets.json")
    assert result == {}


def test_fetch_presets_skips_non_dict_preset():
    """fetch_presets skips preset entries that are not dicts."""
    mock_response = json.dumps(
        {
            "good": {
                "dirs": ["src"],
                "max_tokens": 100,
                "split_mode": "by_file",
                "detect": ["src"],
            },
            "bad": "string_not_object",
        }
    ).encode("utf-8")
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(mock_response)):
        result = fetch_presets("https://example.com/presets.json")
    assert "good" in result
    assert "bad" not in result


def test_fetch_presets_skips_no_detect_no_dirs():
    """fetch_presets skips presets without detect or dirs or command."""
    mock_response = json.dumps(
        {
            "empty": {
                "max_tokens": 100,
                "split_mode": "by_file",
            }
        }
    ).encode("utf-8")
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(mock_response)):
        result = fetch_presets("https://example.com/presets.json")
    assert "empty" not in result


def test_merge_presets_builtin_unchanged_no_remote():
    """merge_presets keeps built-in when remote is empty."""
    builtin = {"python": {"dirs": ["src"], "max_tokens": 16000}}
    remote = {}
    local = {}
    merged = merge_presets(builtin, remote, local)
    assert merged == builtin


def test_merge_presets_remote_updates_builtin():
    """Remote updates built-in presets when local doesn't override."""
    builtin = {"python": {"dirs": ["src"], "max_tokens": 16000}}
    remote = {"python": {"dirs": ["src", "lib"], "max_tokens": 32000}}
    local = {}
    merged = merge_presets(builtin, remote, local)
    assert merged["python"]["dirs"] == ["src", "lib"]
    assert merged["python"]["max_tokens"] == 32000


def test_merge_presets_remote_adds_new():
    """Remote adds new presets not in built-in."""
    builtin = {"python": {"dirs": ["src"], "max_tokens": 16000}}
    remote = {
        "python": {"dirs": ["src"], "max_tokens": 16000},
        "go": {"dirs": ["."], "max_tokens": 16000},
    }
    local = {}
    merged = merge_presets(builtin, remote, local)
    assert "go" in merged
    assert merged["go"]["dirs"] == ["."]


def test_merge_presets_local_wins_over_remote():
    """Local presets never overwritten by remote."""
    builtin = {"python": {"dirs": ["src"], "max_tokens": 16000}}
    remote = {"python": {"dirs": ["src", "lib"], "max_tokens": 32000}}
    local = {"python": {"dirs": ["custom"], "max_tokens": 8000}}
    merged = merge_presets(builtin, remote, local)
    assert merged["python"]["dirs"] == ["custom"]
    assert merged["python"]["max_tokens"] == 8000


def test_merge_presets_local_adds_new():
    """Local presets add new entries."""
    builtin = {"python": {"dirs": ["src"], "max_tokens": 16000}}
    remote = {}
    local = {"my_game": {"dirs": ["game"], "max_tokens": 8000}}
    merged = merge_presets(builtin, remote, local)
    assert "my_game" in merged
    assert merged["my_game"]["dirs"] == ["game"]


def test_merge_presets_local_blocks_remote_override():
    """Remote update to built-in is blocked when local has that preset."""
    builtin = {"python": {"dirs": ["src"], "max_tokens": 16000}}
    remote = {"python": {"dirs": ["src", "vendor"], "max_tokens": 64000}}
    local = {"python": {"dirs": ["my_src"], "max_tokens": 8000}}
    merged = merge_presets(builtin, remote, local)
    assert merged["python"]["dirs"] == ["my_src"]


def test_merge_presets_remote_does_not_override_local():
    """Remote cannot override a preset that exists in local."""
    builtin = {}
    remote = {"my_tool": {"dirs": ["remote_src"], "max_tokens": 16000}}
    local = {"my_tool": {"dirs": ["local_src"], "max_tokens": 8000}}
    merged = merge_presets(builtin, remote, local)
    assert merged["my_tool"]["dirs"] == ["local_src"]


def test_fetch_presets_with_remote_presets_flow():
    """End-to-end: fetch remote, merge with built-in, local wins."""
    builtin = _load_builtin_presets()
    mock_response = json.dumps(
        {
            "python": {
                "dirs": ["src", "lib"],
                "patterns": ["*.py"],
                "max_tokens": 32000,
                "split_mode": "by_file",
                "detect": ["src"],
            },
            "go": {
                "dirs": ["."],
                "patterns": ["*.go"],
                "files": ["go.mod"],
                "max_tokens": 16000,
                "split_mode": "by_file",
                "detect": ["go.mod"],
            },
        }
    ).encode("utf-8")

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(mock_response)):
        remote = fetch_presets("https://example.com/presets.json")

    local = {}
    merged = merge_presets(builtin, remote, local)
    assert "python" in merged
    assert "go" in merged
    assert merged["python"]["max_tokens"] == 32000
