# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Dataclass configuration types for arachna.

ProfileConfig replaces dict-based profile access with typed fields.
ArachnaConfig wraps the top-level .arachna.json structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .defaults import DEFAULT_EXCLUDE

DEFAULT_PATTERNS = ["*.py", "*.md", "*.yaml", "*.yml", "*.toml", "*.json", "*.cfg", "*.ini"]


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

    @classmethod
    def from_dict(cls, d: dict) -> ProfileConfig:
        """Construct ProfileConfig from dict, filling defaults for missing keys."""
        defaults = cls()
        return cls(
            name_template=d.get("name_template", defaults.name_template),
            title_template=d.get("title_template", defaults.title_template),
            max_tokens=d.get("max_tokens", defaults.max_tokens),
            split_mode=d.get("split_mode", defaults.split_mode),
            directories=d.get("directories", defaults.directories),
            patterns=d.get("patterns", defaults.patterns),
            files=d.get("files", defaults.files),
            exclude_patterns=d.get("exclude_patterns", defaults.exclude_patterns),
            pre_commands=d.get("pre_commands", defaults.pre_commands),
            post_commands=d.get("post_commands", defaults.post_commands),
            command=d.get("command"),
            section_format=d.get("section_format", defaults.section_format),
            compress=d.get("compress", defaults.compress),
            include_binary=d.get("include_binary", defaults.include_binary),
            binary_extensions=d.get("binary_extensions"),
            binary_max_mb=d.get("binary_max_mb", defaults.binary_max_mb),
            tokenizer=d.get("tokenizer", defaults.tokenizer),
            chars_per_token=d.get("chars_per_token"),
            line_numbers=d.get("line_numbers", defaults.line_numbers),
            extends=d.get("extends"),
            remote=d.get("remote", defaults.remote),
            use_gitignore=d.get("use_gitignore", defaults.use_gitignore),
            split_marker=d.get("split_marker", defaults.split_marker),
            _explicit_keys=set(d.keys()),
        )


DEFAULT_PROFILE_CONFIG = ProfileConfig()


@dataclass
class ArachnaConfig:
    """Top-level arachna configuration (.arachna.json)."""

    project_name: str = "Project"
    output_dir: str = "arachna_context"
    tokenizer: str = "default"
    profiles: dict[str, ProfileConfig] = field(default_factory=dict)
    _root: str | None = None
