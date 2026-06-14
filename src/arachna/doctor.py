# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Doctor — validates config and collected context integrity."""

from pathlib import Path

from .config import load_config
from .gitignore import load_gitignore_patterns
from .validator import validate_profile


def run_doctor(project_root: Path | None = None, config: dict | None = None) -> dict:
    """Run diagnostic checks on the project configuration.

    Args:
        project_root: Project root directory for gitignore checks.
        config: Pre-loaded config dict. If None, loads from project_root or cwd.

    Returns dict with:
        profiles: dict of profile_name -> {errors, warnings}
        gitignore: list of gitignore warnings
        total_errors, total_warnings: ints
    """
    if project_root is None:
        project_root = Path.cwd()

    result = {
        "profiles": {},
        "gitignore": [],
        "total_errors": 0,
        "total_warnings": 0,
    }

    if config is None:
        config = load_config(root=project_root)

    profiles = config.get("profiles", {})

    if not profiles:
        profiles = {"default": {"max_tokens": 32000, "split_mode": "by_file", "directories": ["."]}}

    for name, profile in profiles.items():
        validation = validate_profile(name, profile)
        result["profiles"][name] = {
            "errors": validation["errors"],
            "warnings": validation["warnings"],
        }
        result["total_errors"] += len(validation["errors"])
        result["total_warnings"] += len(validation["warnings"])

    # Gitignore checks
    if project_root.is_dir():
        try:
            patterns = load_gitignore_patterns(project_root)
            if patterns:
                result["gitignore"].append(f"Loaded {len(patterns)} gitignore patterns")
        except (OSError, ValueError) as e:
            result["gitignore"].append(f"Error loading .gitignore: {e}")
            result["total_warnings"] += 1
    else:
        result["gitignore"].append("Project root is not a directory, skipping .gitignore check")
        result["total_warnings"] += 1

    return result


def print_doctor(report: dict):
    """Print doctor report to stdout."""
    print("arachna doctor — configuration diagnostic\n")
    print(f"Profiles: {len(report['profiles'])}")
    print(f"Errors: {report['total_errors']}")
    print(f"Warnings: {report['total_warnings']}")

    for name, info in report["profiles"].items():
        errors = info["errors"]
        warnings = info["warnings"]
        if errors or warnings:
            print(f"\n[{name}]")
            for e in errors:
                print(f"  ✗ {e}")
            for w in warnings:
                print(f"  ⚠ {w}")
        else:
            print(f"  [{name}] ✓ healthy")

    if report["gitignore"]:
        print()
        for msg in report["gitignore"]:
            print(f"  ℹ {msg}")

    if report["total_errors"] == 0:
        print("\n✓ All profiles valid")
    else:
        print(f"\n✗ {report['total_errors']} error(s) found")
