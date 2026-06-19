# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Interactive .arachna.json bootstrap."""

import json
from pathlib import Path

from ..domain.atomic_write import atomic_write_text
from ..domain.path_utils import SafePath
from .presets import _SEPARATOR, detect_presets, preset_to_profile


def _ask(prompt: str, default: str) -> str:
    try:
        value = input(f"{prompt} [{default}]: ").strip()
    except EOFError:
        return default
    return value if value else default


def _ask_yes(prompt: str, default: bool = True) -> bool:
    suffix = "Y/n" if default else "y/N"
    try:
        answer = input(f"{prompt} [{suffix}]: ").strip().lower()
    except EOFError:
        return default
    if not answer:
        return default
    return answer in ("y", "yes")


def _validate_output_dir(output_dir):
    """Reject output_dir values containing path separators or traversal."""
    if not output_dir or ".." in output_dir or "/" in output_dir or "\\" in output_dir:
        raise ValueError(
            f"Invalid output_dir: '{output_dir}'. Must be a simple directory name without path separators."
        )


def run_defaults(output_dir: str = ".", preset: str | None = None, root: Path | None = None):
    if root is None:
        root = Path.cwd()
    project_name = root.resolve().name
    config = {"project_name": project_name, "output_dir": output_dir, "profiles": {}}
    detected = detect_presets(preset_name=preset, root=root)
    if not detected:
        print("Warning: no presets detected for this project.")
        print("  You can create a custom preset in presets.json.")
        print("  Run 'arachna --init' for interactive setup.")
    for name in detected:
        profile = preset_to_profile(name)
        if profile:
            config["profiles"][name] = profile
    _write_config(root, config, output_dir)
    if detected:
        print(f"Profiles: {', '.join(config['profiles'].keys())}")


def _collect_interactive_profiles(detected, max_tokens):
    profiles = {}
    for name in detected:
        profile = preset_to_profile(name)
        if profile is None:
            continue
        profile["max_tokens"] = max_tokens
        dirs = profile.get("directories", [])
        files = profile.get("files", [])
        if dirs:
            print(f"  {name} dirs: {', '.join(dirs)}")
        if files:
            print(f"  {name} files: {', '.join(files)}")
        if not dirs and not files and name != "git":
            print(f"  {name}: (command-based)")
        if _ask_yes(f"  Add '{name}' profile?", default=True):
            profiles[name] = profile
    return profiles


def run_interactive(output_dir: str = ".", preset: str | None = None, root: Path | None = None):
    if root is None:
        root = Path.cwd()
    from .config import find_config

    existing = find_config(root=root)
    if existing:
        print(f"Found existing config: {existing}")
        if not _ask_yes("Overwrite?", default=False):
            print("Aborted.")
            return
    project_name = _ask("Project name", root.resolve().name)
    output_dir = _ask("Output directory", output_dir)
    max_tokens = int(_ask("Default max tokens", "16000"))
    print()
    print(_SEPARATOR)
    print("Detected:")
    print(_SEPARATOR)
    detected = detect_presets(preset_name=preset, root=root)
    profiles = _collect_interactive_profiles(detected, max_tokens)
    config = {"project_name": project_name, "output_dir": output_dir, "profiles": profiles}
    print()
    print(_SEPARATOR)
    print(json.dumps(config, indent=2))
    print(_SEPARATOR)
    if _ask_yes("Create this config?", default=True):
        _write_config(root, config, output_dir)


def _write_config(root: Path, config: dict, output_dir: str):
    _validate_output_dir(output_dir)
    cfg_path = SafePath(root / ".arachna.json", root)
    atomic_write_text(cfg_path.to_path(), json.dumps(config, indent=2) + "\n")
    print(f"Created {cfg_path}")
    out_path = SafePath(root / output_dir, root)
    out_path.mkdir(parents=True, exist_ok=True)
    print(f"Created {out_path}/")
    print("Done. Run 'arachna --all' to collect context.")
