"""Config loader — reads .arachna.json from project root."""

import json
from pathlib import Path
from typing import Any

DEFAULT_EXCLUDE = [
    "*__pycache__*",
    "*.pyc",
    "*.egg-info*",
    ".git",
    ".git/*",
    "venv",
    "venv/*",
    "node_modules",
    "node_modules/*",
    ".DS_Store",
]

DEFAULT_PATTERNS = ["*.py", "*.md", "*.yaml", "*.yml", "*.toml", "*.json", "*.cfg", "*.ini"]


def find_config() -> Path | None:
    """Find .arachna.json in current or parent directories."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        cfg = parent / ".arachna.json"
        if cfg.exists():
            return cfg
    return None


def load_config() -> dict[str, Any]:
    """Load configuration from .arachna.json."""
    cfg_path = find_config()
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
        "output_dir": ".",
        "profiles": {},
    }


def get_profile(name: str) -> dict[str, Any]:
    """Load config and return specific profile."""
    config = load_config()
    profiles = config.get("profiles", {})

    # Default profile when none configured
    if not profiles:
        return _default_profile()

    if name not in profiles:
        raise KeyError(f"Profile '{name}' not found. Available: {list(profiles.keys())}")
    profile = profiles[name]
    profile.setdefault("name_template", f"chat-{name}")
    profile.setdefault(
        "title_template",
        f"# {config['project_name']} — {name.upper()} (part {{part}})\n\n",
    )
    profile.setdefault("max_tokens", 16000)
    profile.setdefault("split_mode", "by_file")
    profile.setdefault("directories", [])
    profile.setdefault("patterns", ["*"])
    profile.setdefault("files", [])
    profile.setdefault("pre_commands", [])
    profile.setdefault("command", None)
    profile.setdefault("exclude_patterns", DEFAULT_EXCLUDE.copy())
    profile.setdefault("split_marker", "\n\n")
    return profile


def _default_profile() -> dict[str, Any]:
    """Return a sensible default profile when none configured."""
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
    }
