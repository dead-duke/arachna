"""CLI entry point for arachna."""

import argparse
import sys
from pathlib import Path

from .collector import collect
from .config import get_profile, load_config
from .gatherer import dry_run
from .renderer import render_dry_run
from .validator import validate_profile


def _list_profiles(config: dict) -> list[str]:
    """Get list of profile names, falling back to default if empty."""
    profiles = config.get("profiles", {})
    if profiles:
        return list(profiles.keys())
    return ["default"]


def main():
    parser = argparse.ArgumentParser(description="arachna — context collector for AI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--profile", "-p", help="Profile name to collect")
    group.add_argument("--all", "-a", action="store_true", help="Collect all profiles")
    group.add_argument("--clean", "-c", action="store_true", help="Remove all collected files")
    group.add_argument("--list", "-l", action="store_true", help="List available profiles")
    group.add_argument("--validate", action="store_true", help="Validate config for errors")

    parser.add_argument(
        "--dry-run", action="store_true", help="Show what will be collected without writing files"
    )
    parser.add_argument("--output-dir", "-o", help="Override output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show skipped files")

    args = parser.parse_args()

    config = load_config()
    project_name = config.get("project_name", "Project")
    output_dir = args.output_dir or config.get("output_dir", ".")

    if args.list:
        profile_names = _list_profiles(config)
        for name in profile_names:
            try:
                prof = get_profile(name)
            except KeyError:
                continue
            cmd = prof.get("command")
            if cmd:
                print(f"  {name}: command ({prof.get('max_tokens', '?')} tokens)")
            else:
                dirs = len(prof.get("directories", []))
                files = len(prof.get("files", []))
                print(
                    f"  {name}: {dirs} dirs, {files} files ({prof.get('max_tokens', '?')} tokens)"
                )
        return

    if args.validate:
        profiles = config.get("profiles", {})
        if not profiles:
            profiles = {"default": get_profile("default")}

        all_errors = 0
        all_warnings = 0
        for name, prof in profiles.items():
            if name == "default" and not config.get("profiles"):
                result = validate_profile(name, prof)
            else:
                result = validate_profile(name, prof)

            errors = result["errors"]
            warnings = result["warnings"]

            if errors or warnings:
                print(f"\n[{name}]")
                for e in errors:
                    print(f"  ✗ {e}")
                for w in warnings:
                    print(f"  ⚠ {w}")
                all_errors += len(errors)
                all_warnings += len(warnings)
            else:
                print(f"  [{name}] ✓ valid")

        print(f"\nResult: {all_errors} error(s), {all_warnings} warning(s)")
        sys.exit(1 if all_errors > 0 else 0)

    if args.clean:
        cleaned = 0
        for name in _list_profiles(config):
            try:
                prof = get_profile(name)
            except KeyError:
                continue
            tmpl = prof.get("name_template", f"chat-{name}")
            for f in Path(output_dir).glob(f"{tmpl}_*.md"):
                f.unlink()
                cleaned += 1
                print(f"  Removed: {f}")
        print(f"Cleaned {cleaned} file(s).")
        return

    profiles_to_run = _list_profiles(config) if args.all else [args.profile]

    if not profiles_to_run:
        print("No profiles to collect.")
        sys.exit(1)

    if args.dry_run:
        all_stats = []
        for name in profiles_to_run:
            try:
                profile = get_profile(name)
            except KeyError as e:
                print(f"Error: {e}")
                sys.exit(1)
            stats = dry_run(profile)
            stats["name"] = name
            all_stats.append(stats)
        render_dry_run(all_stats)
        return

    for name in profiles_to_run:
        try:
            profile = get_profile(name)
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)

        print(f"[{name}] Collecting...")
        created = collect(profile, project_name, output_dir, verbose=args.verbose)
        if created:
            for f in created:
                lines = Path(f).read_text(encoding="utf-8").count("\n") + 1
                print(f"  {f} ({lines} lines)")
        else:
            print("  No content collected.")


if __name__ == "__main__":
    main()
