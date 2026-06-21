# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Dataclass configuration types for arachna.

ProfileConfig replaces dict-based profile access with typed fields.
ArachnaConfig wraps the top-level .arachna.json structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_PATTERNS = ["*.py", "*.md", "*.yaml", "*.yml", "*.toml", "*.json", "*.cfg", "*.ini"]

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


@dataclass
class ProfileConfig:
    """Typed configuration for a single collection profile.

    All fields have sensible defaults. _explicit_keys tracks which fields
    were explicitly set in .arachna.json (used by extends merging).
    Validation is done separately by validator.validate_profile().
    """

    name_template: str = "chat-default"
    title_template: str = "# Project — DEFAULT (part {part})\n\n"
    max_tokens: int = 32000
    split_mode: str = "by_file"
    directories: list[str] = field(default_factory=lambda: ["."])
    patterns: list[str] = field(default_factory=lambda: DEFAULT_PATTERNS.copy())
    files: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=lambda: DEFAULT_EXCLUDE.copy())
    pre_commands: list[str] = field(default_factory=list)
    post_commands: list[str] = field(default_factory=list)
    command: str | None = None
    section_format: str = "markdown"
    compress: bool = False
    include_binary: bool = False
    binary_extensions: list[str] | None = None
    binary_max_mb: float = 1.0
    tokenizer: str = "default"
    chars_per_token: int | None = None
    line_numbers: bool = False
    extends: str | None = None
    remote: bool = False
    use_gitignore: bool = True
    split_marker: str = "\n\n"
    _explicit_keys: set = field(default_factory=set)

    def to_dict(self) -> dict:
        """Convert back to dict for internal consumers that still expect dict."""
        return {
            "name_template": self.name_template,
            "title_template": self.title_template,
            "max_tokens": self.max_tokens,
            "split_mode": self.split_mode,
            "directories": self.directories,
            "patterns": self.patterns,
            "files": self.files,
            "exclude_patterns": self.exclude_patterns,
            "pre_commands": self.pre_commands,
            "post_commands": self.post_commands,
            "command": self.command,
            "section_format": self.section_format,
            "compress": self.compress,
            "include_binary": self.include_binary,
            "binary_extensions": self.binary_extensions,
            "binary_max_mb": self.binary_max_mb,
            "tokenizer": self.tokenizer,
            "chars_per_token": self.chars_per_token,
            "line_numbers": self.line_numbers,
            "extends": self.extends,
            "remote": self.remote,
            "use_gitignore": self.use_gitignore,
            "split_marker": self.split_marker,
        }


DEFAULT_PROFILE_CONFIG = ProfileConfig()


@dataclass
class ArachnaConfig:
    """Top-level arachna configuration (.arachna.json)."""

    project_name: str = "Project"
    output_dir: str = "arachna_context"
    tokenizer: str = "default"
    profiles: dict[str, ProfileConfig] = field(default_factory=dict)
    _root: str | None = None
