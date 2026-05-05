"""CLI entry point for arachna."""

import argparse
import sys
from pathlib import Path

from .collector import collect
from .config import get_profile, load_config
from .gatherer import dry_run
from .renderer import render_dry_run


def main():
    parser = argparse.ArgumentParser(description="arachna — context collector for AI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--profile", "-p", help="Profile name to collect")
    group.add_argument("--all", "-a", action="store_true", help="Collect all profiles")
    group.add_argument("--clean", "-c", action="store_true", help="Remove all collected files")
    group.add_argument("--list", "-l", action="store_true", help="List available profiles")

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
        profiles = config.get("profiles", {})
        if not profiles:
            print("No profiles configured.")
        else:
            for name, prof in profiles.items():
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

    if args.clean:
        cleaned = 0
        profiles = config.get("profiles", {})
        for prof in profiles.values():
            tmpl = prof.get("name_template", "chat")
            for f in Path(output_dir).glob(f"{tmpl}_*.md"):
                f.unlink()
                cleaned += 1
                print(f"  Removed: {f}")
        print(f"Cleaned {cleaned} file(s).")
        return

    profiles_to_run = list(config.get("profiles", {}).keys()) if args.all else [args.profile]

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
