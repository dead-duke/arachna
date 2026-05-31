"""Tests for external presets with explicit preset_name.

Covers the LOW finding from AUDIT_REPORT.md: missing test coverage
for detect_presets and preset_to_profile with external presets
and preset_name parameter.
"""

import json

from arachna.presets import detect_presets, preset_to_profile


def test_detect_presets_explicit_external_with_name(tmp_path, monkeypatch):
    """Explicit preset_name with external presets checks detect-paths."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "game").mkdir()
    (tmp_path / "game" / "main.lua").write_text("x")

    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "my_game": {
                    "dirs": ["game"],
                    "patterns": ["*.lua"],
                    "max_tokens": 8000,
                    "split_mode": "by_file",
                    "detect": ["game"],
                }
            }
        )
    )
    detected = detect_presets(preset_name="my_game", external_path=f)
    assert detected == ["my_game"]


def test_detect_presets_explicit_external_no_match(tmp_path, monkeypatch):
    """Explicit preset_name with external presets returns empty if no match."""
    monkeypatch.chdir(tmp_path)

    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "my_game": {
                    "dirs": ["game"],
                    "patterns": ["*.lua"],
                    "max_tokens": 8000,
                    "split_mode": "by_file",
                    "detect": ["game"],
                }
            }
        )
    )
    detected = detect_presets(preset_name="my_game", external_path=f)
    assert detected == []


def test_preset_to_profile_external_with_name(tmp_path, monkeypatch):
    """preset_to_profile with external presets and explicit name."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "game").mkdir()
    (tmp_path / "game" / "main.lua").write_text("x")

    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "my_game": {
                    "dirs": ["game"],
                    "patterns": ["*.lua"],
                    "max_tokens": 8000,
                    "split_mode": "by_file",
                }
            }
        )
    )
    profile = preset_to_profile("my_game", external_path=f)
    assert profile is not None
    assert profile["split_mode"] == "by_file"
    assert "game" in profile["directories"]
    assert "*.lua" in profile["patterns"]


def test_detect_presets_explicit_external_service_always_allowed(tmp_path, monkeypatch):
    """External service-like preset with empty detect is always allowed with explicit name."""
    monkeypatch.chdir(tmp_path)

    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "my_tool": {
                    "command": "echo hi",
                    "max_tokens": 1000,
                    "split_mode": "by_file",
                    "detect": [],
                }
            }
        )
    )
    detected = detect_presets(preset_name="my_tool", external_path=f)
    assert detected == ["my_tool"]


def test_detect_presets_explicit_external_unknown_name(tmp_path, monkeypatch):
    """Explicit preset_name not in external presets returns empty list."""
    monkeypatch.chdir(tmp_path)

    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "my_game": {
                    "dirs": ["game"],
                    "patterns": ["*.lua"],
                    "max_tokens": 8000,
                    "split_mode": "by_file",
                    "detect": ["game"],
                }
            }
        )
    )
    detected = detect_presets(preset_name="nonexistent", external_path=f)
    assert detected == []
