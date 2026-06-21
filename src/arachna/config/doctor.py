"""Doctor — validates config and collected context integrity."""

from pathlib import Path

from ..domain.execution.gitignore import load_gitignore_patterns
from .core.config import load_config
from .core.validator import validate_profile
from .profile_config import ProfileConfig


def run_doctor(project_root: Path | None = None, config: dict | None = None) -> dict:
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

    profiles = config.profiles if hasattr(config, "profiles") else config.get("profiles", {})

    if not profiles:
        profiles = {
            "default": ProfileConfig(max_tokens=32000, split_mode="by_file", directories=["."])
        }

    for name, profile in profiles.items():
        validation = validate_profile(name, profile)
        result["profiles"][name] = {
            "errors": validation["errors"],
            "warnings": validation["warnings"],
        }
        result["total_errors"] += len(validation["errors"])
        result["total_warnings"] += len(validation["warnings"])

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


def _print_profile_results(profiles):
    for name, info in profiles.items():
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


def print_doctor(report: dict):
    print("arachna doctor — configuration diagnostic\n")
    print(f"Profiles: {len(report['profiles'])}")
    print(f"Errors: {report['total_errors']}")
    print(f"Warnings: {report['total_warnings']}")

    _print_profile_results(report["profiles"])

    if report["gitignore"]:
        print()
        for msg in report["gitignore"]:
            print(f"  ℹ {msg}")

    if report["total_errors"] == 0:
        print("\n✓ All profiles valid")
    else:
        print(f"\n✗ {report['total_errors']} error(s) found")
