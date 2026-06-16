# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Config loader — reads .arachna.json from project root."""

import json
from pathlib import Path
from typing import Any

_COMMON_EXCLUDE_DIRS = frozenset(
    {
        ".git",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "venv",
        "node_modules",
    }
)

DEFAULT_EXCLUDE = ["*__pycache__*", "*.pyc", "*.egg-info*", ".DS_Store"]
for _d in sorted(_COMMON_EXCLUDE_DIRS):
    DEFAULT_EXCLUDE.extend([_d, f"{_d}/*"])

DEFAULT_PATTERNS = ["*.py", "*.md", "*.yaml", "*.yml", "*.toml", "*.json", "*.cfg", "*.ini"]

_MERGE_APPEND = {"exclude_patterns", "patterns"}
_MAX_EXTENDS_DEPTH = 5


def find_config(root: Path) -> Path | None:
    """Find .arachna.json by walking up from root."""
    for parent in [root, *root.parents]:
        cfg = parent / ".arachna.json"
        if cfg.exists():
            return cfg
    return None


def load_config(root: Path) -> dict[str, Any]:
    """Load config from .arachna.json found from root."""
    cfg_path = find_config(root)
    if not cfg_path:
        return _default_config()
    with open(cfg_path, encoding="utf-8") as f:
        data = json.load(f)
    defaults = _default_config()
    defaults.update(data)
    return defaults


def _default_config() -> dict[str, Any]:
    return {
        "project_name": "Project",
        "output_dir": "arachna_context",
        "tokenizer": "default",
        "profiles": {},
    }


def _resolve_profile(name: str, profiles: dict, depth: int = 0) -> dict[str, Any]:
    if depth > _MAX_EXTENDS_DEPTH:
        raise ValueError(
            f"Circular or too deep extends chain for profile '{name}' (max depth {_MAX_EXTENDS_DEPTH})"
        )
    if name not in profiles:
        raise KeyError(f"Profile '{name}' not found. Available: {list(profiles.keys())}")
    profile = dict(profiles[name])
    if "extends" in profile:
        parent_name = profile.pop("extends")
        parent = _resolve_profile(parent_name, profiles, depth + 1)
        profile = _merge_profiles(parent, profile)
    return profile


def _merge_profiles(base: dict, child: dict) -> dict:
    merged = dict(base)
    for key, value in child.items():
        if key in _MERGE_APPEND and key in merged:
            merged[key] = merged[key] + value
        else:
            if key in merged and key not in _MERGE_APPEND and merged[key] != value:
                print(
                    f"  Warning: profile field '{key}' overridden by child (parent: {merged[key]}, child: {value})"
                )
            merged[key] = value
    return merged


def get_profile(name: str, root: Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Get profile by name from config. Falls back to load_config(root) if config is None."""
    if config is None:
        config = load_config(root)
    project_name = config.get("project_name", "Project")
    profiles = config.get("profiles", {})
    if not profiles:
        return _default_profile()
    if name not in profiles:
        raise KeyError(f"Profile '{name}' not found. Available: {list(profiles.keys())}")
    profile = _resolve_profile(name, profiles)
    profile.setdefault("name_template", f"chat-{name}")
    profile.setdefault("title_template", f"# {project_name} — {name.upper()} (part {{part}})\n\n")
    profile.setdefault("max_tokens", 16000)
    profile.setdefault("split_mode", "by_file")
    profile.setdefault("directories", [])
    profile.setdefault("patterns", ["*"])
    profile.setdefault("files", [])
    profile.setdefault("pre_commands", [])
    profile.setdefault("command", None)
    profile.setdefault("exclude_patterns", DEFAULT_EXCLUDE.copy())
    profile.setdefault("split_marker", "\n\n")
    profile.setdefault("tokenizer", "default")
    profile.setdefault("line_numbers", False)
    return profile


def _default_profile() -> dict[str, Any]:
    return {
        "name_template": "chat-default",
        "title_template": "# Project — DEFAULT (part {part})\n\n",
        "max_tokens": 32000,
        "split_mode": "by_file",
        "directories": ["."],
        "patterns": DEFAULT_PATTERNS.copy(),
        "exclude_patterns": DEFAULT_EXCLUDE.copy(),
        "pre_commands": ["tree -I '__pycache__|*.pyc|*.egg-info|venv|.git' || ls -la"],
        "split_marker": "\n\n",
        "tokenizer": "default",
        "line_numbers": False,
    }
