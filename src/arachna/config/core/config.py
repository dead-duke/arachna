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
            profiles[name] = ProfileConfig.from_dict(prof_dict)
    return ArachnaConfig(
        project_name=data.get("project_name", "Project"),
        output_dir=data.get("output_dir", "arachna_context"),
        tokenizer=data.get("tokenizer", "default"),
        profiles=profiles,
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
    return ProfileConfig.from_dict(merged)


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
