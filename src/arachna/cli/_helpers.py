# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Shared helpers for CLI handlers."""

import copy
from pathlib import Path

from ..config.profile_config import ArachnaConfig, ProfileConfig
from ..domain.atomic_write import atomic_write_text
from ..domain.path_utils import SafePath
from ..domain.tokenizer import count_tokens


def get_root(config: ArachnaConfig | dict) -> Path:
    """Extract project root from config, falling back to current directory."""
    if isinstance(config, ArachnaConfig):
        return Path(config._root) if config._root else Path.cwd()
    return Path(config.get("_root", Path.cwd()))


def list_profiles(config: ArachnaConfig | dict) -> list[str]:
    profiles = config.profiles if isinstance(config, ArachnaConfig) else config.get("profiles", {})
    if profiles:
        return list(profiles.keys())
    return ["default"]


def apply_args_to_profile(profile: ProfileConfig, args) -> ProfileConfig:
    profile = copy.deepcopy(profile)
    if getattr(args, "compress", False):
        profile.compress = True
    if getattr(args, "format", None):
        profile.section_format = args.format
    return profile


def parse_output_dir(args, config: ArachnaConfig | dict) -> str:
    if getattr(args, "output_dir", None):
        return args.output_dir
    if isinstance(config, ArachnaConfig):
        return config.output_dir
    return config.get("output_dir", ".")


def print_collected(created: list[str]):
    if created:
        for f in created:
            fp = Path(f)
            content = fp.read_text(encoding="utf-8")
            lines = content.count("\n") + 1
            tokens = count_tokens(content)
            print(f"  {fp.name} ({lines} lines, ~{tokens} tokens)")
    else:
        print("  No content collected.")


def write_manifest(
    out_path: SafePath,
    all_files: list[str],
    tokens_by_file: dict[str, int],
    config: ArachnaConfig | dict,
):
    project_name = (
        config.project_name
        if isinstance(config, ArachnaConfig)
        else config.get("project_name", "Project")
    )
    lines = [
        f"# {project_name} — MANIFEST\n",
        "\nAll collected files:\n",
    ]
    for f in sorted(all_files):
        tokens = tokens_by_file.get(f, 0)
        lines.append(f"  {f} (~{tokens} tokens)")
    lines.append(f"\nTotal: {len(all_files)} file(s)\n")
    mf = out_path / "chat-manifest.md"
    atomic_write_text(mf.to_path(), "\n".join(lines))
    print(f"  chat-manifest.md ({len(all_files)} files)")


def format_profile_section(profile_dict: dict) -> str:
    """Format profile dict fields for display. Used in snapshot info."""
    lines = []
    for key, label in [
        ("directories", "directories"),
        ("patterns", "patterns"),
        ("files", "files"),
        ("pre_commands", "pre_commands"),
    ]:
        val = profile_dict.get(key, [])
        if val:
            lines.append(f"  {label}: {', '.join(val)}")
    lines.append(f"  max_tokens: {profile_dict.get('max_tokens', '?')}")
    lines.append(f"  split_mode: {profile_dict.get('split_mode', '?')}")
    return "\n".join(lines)
