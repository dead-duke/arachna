"""Config loader — reads .arachna.json from project root."""

import json
from pathlib import Path

from ..profile_config import DEFAULT_PROFILE_CONFIG, ArachnaConfig, ProfileConfig

_MAX_EXTENDS_DEPTH = 5
_MERGE_APPEND = {"exclude_patterns", "patterns"}


def find_config(root: Path) -> Path | None:
    for parent in [root, *root.parents]:
        cfg = parent / ".arachna.json"
        if cfg.exists():
            return cfg
    return None


def load_config(root: Path) -> ArachnaConfig:
    cfg_path = find_config(root)
    if not cfg_path:
        return ArachnaConfig()
    with open(cfg_path, encoding="utf-8") as f:
        data = json.load(f)
    profiles_raw = data.get("profiles", {})
    profiles = {}
    for name, prof_dict in profiles_raw.items():
        if isinstance(prof_dict, dict):
            profiles[name] = _dict_to_profile(prof_dict)
    return ArachnaConfig(
        project_name=data.get("project_name", "Project"),
        output_dir=data.get("output_dir", "arachna_context"),
        tokenizer=data.get("tokenizer", "default"),
        profiles=profiles,
    )


def _dict_to_profile(d: dict) -> ProfileConfig:
    defaults = ProfileConfig()
    return ProfileConfig(
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


def _resolve_profile(name: str, profiles: dict, depth: int = 0) -> ProfileConfig:
    if depth > _MAX_EXTENDS_DEPTH:
        raise ValueError(
            f"Circular or too deep extends chain for profile '{name}' (max depth {_MAX_EXTENDS_DEPTH})"
        )
    if name not in profiles:
        raise KeyError(f"Profile '{name}' not found. Available: {list(profiles.keys())}")
    profile = profiles[name]
    if profile.extends:
        parent_name = profile.extends
        parent = _resolve_profile(parent_name, profiles, depth + 1)
        profile = _merge_profiles(parent, profile)
    return profile


def _merge_profiles(base: ProfileConfig, child: ProfileConfig) -> ProfileConfig:
    merged = base.to_dict()
    for key in child._explicit_keys:
        if key == "extends":
            continue
        if key in _MERGE_APPEND:
            if key in base._explicit_keys:
                merged[key] = merged.get(key, []) + getattr(child, key)
            else:
                merged[key] = getattr(child, key)
        else:
            merged[key] = getattr(child, key)
    return _dict_to_profile(merged)


def get_profile(name: str, root: Path, config: ArachnaConfig | None = None) -> ProfileConfig:
    if config is None:
        config = load_config(root)
    project_name = config.project_name
    profiles = config.profiles
    if not profiles:
        return DEFAULT_PROFILE_CONFIG
    if name not in profiles:
        raise KeyError(f"Profile '{name}' not found. Available: {list(profiles.keys())}")
    profile = _resolve_profile(name, profiles)
    if "name_template" not in profile._explicit_keys:
        profile.name_template = f"chat-{name}"
    if "title_template" not in profile._explicit_keys:
        profile.title_template = f"# {project_name} — {name.upper()} (part {{part}})\n\n"
    return profile
