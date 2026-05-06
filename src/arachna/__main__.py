"""CLI entry point for arachna."""

import argparse
import json
import sys
from pathlib import Path

from .collector import _MANIFEST, clean_manifest, collect, load_manifest, save_manifest
from .config import get_profile, load_config
from .gatherer import dry_run
from .renderer import render_dry_run
from .tokenizer import count_tokens
from .validator import validate_profile


def _list_profiles(config: dict) -> list[str]:
    profiles = config.get("profiles", {})
    if profiles:
        return list(profiles.keys())
    return ["default"]


def main():
    if "--completion" in sys.argv:
        from .completion import main as completion_main

        idx = sys.argv.index("--completion")
        shell = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
        sys.argv = ["completion", shell]
        completion_main()
        return

    parser = argparse.ArgumentParser(description="arachna — context collector for AI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--profile", "-p", help="Profile name to collect")
    group.add_argument("--all", "-a", action="store_true", help="Collect all profiles")
    group.add_argument("--clean", "-c", action="store_true", help="Remove all collected files")
    group.add_argument("--list", "-l", action="store_true", help="List available profiles")
    group.add_argument("--validate", action="store_true", help="Validate config for errors")
    group.add_argument("--init", action="store_true", help="Create .arachna.json interactively")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what will be collected without writing"
    )
    parser.add_argument("--output-dir", "-o", help="Override output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show skipped files")
    parser.add_argument(
        "--compress", action="store_true", help="Compress whitespace to save tokens"
    )
    parser.add_argument("--incremental", action="store_true", help="Only collect changed files")
    parser.add_argument("--format", choices=["markdown", "xml", "json"], help="Output format")
    parser.add_argument("--defaults", action="store_true", help="Use defaults with --init")

    args = parser.parse_args()
    config = load_config()
    project_name = config.get("project_name", "Project")
    output_dir = args.output_dir or config.get("output_dir", ".")
    out_path = Path(output_dir)

    if args.init:
        from .init import run_defaults, run_interactive

        if args.defaults:
            run_defaults(output_dir)
        else:
            run_interactive(output_dir)
    elif args.list:
        _cmd_list(config)
    elif args.validate:
        _cmd_validate(config)
    elif args.clean:
        _cmd_clean(config, out_path)
    elif args.dry_run:
        _cmd_dry_run(config, args)
    elif args.all:
        _cmd_all(config, args, project_name, out_path)
    else:
        _cmd_single(config, args, project_name, out_path)


def _cmd_list(config: dict):
    for name in _list_profiles(config):
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
            print(f"  {name}: {dirs} dirs, {files} files ({prof.get('max_tokens', '?')} tokens)")


def _cmd_validate(config: dict):
    profiles = config.get("profiles", {})
    if not profiles:
        profiles = {"default": get_profile("default")}
    all_errors = 0
    all_warnings = 0
    for name, prof in profiles.items():
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


def _cmd_clean(config: dict, out_path: Path):
    cleaned = 0
    mf = out_path / _MANIFEST
    if mf.exists():
        try:
            manifest = json.loads(mf.read_text())
            for f in manifest.get("files", []):
                p = Path(f)
                if p.exists():
                    p.unlink()
                    cleaned += 1
                    print(f"  Removed: {f}")
        except (json.JSONDecodeError, OSError):
            pass
        mf.unlink()
        cleaned += 1
        print(f"  Removed: {_MANIFEST}")
    for name in _list_profiles(config):
        try:
            prof = get_profile(name)
        except KeyError:
            continue
        tmpl = prof.get("name_template", f"chat-{name}")
        for f in out_path.glob(f"{tmpl}_*.md"):
            f.unlink()
            cleaned += 1
            print(f"  Removed: {f.name}")
        plain = out_path / f"{tmpl}.md"
        if plain.exists():
            plain.unlink()
            cleaned += 1
            print(f"  Removed: {plain.name}")
    print(f"Cleaned {cleaned} file(s).")


def _cmd_dry_run(config: dict, args):
    profiles_to_run = _list_profiles(config) if args.all else [args.profile]
    all_stats = []
    for name in profiles_to_run:
        try:
            profile = get_profile(name)
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)
        if args.compress:
            profile["compress"] = True
        if args.format:
            profile["section_format"] = args.format
        stats = dry_run(profile)
        stats["name"] = name
        all_stats.append(stats)
    render_dry_run(all_stats)


def _print_result(f: str):
    content = Path(f).read_text(encoding="utf-8")
    lines = content.count("\n") + 1
    tokens = count_tokens(content)
    print(f"  {Path(f).name} ({lines} lines, ~{tokens} tokens)")


def _write_manifest(out_path: Path, all_files: list[str], config: dict):
    """Write chat-manifest.md with summary of all collected files."""
    lines = [
        f"# {config.get('project_name', 'Project')} — MANIFEST\n",
        "\nAll collected files:\n",
    ]
    for f in sorted(all_files):
        p = Path(f)
        if p.exists():
            content = p.read_text(encoding="utf-8")
            tokens = count_tokens(content)
            lines.append(f"  {f} (~{tokens} tokens)")
    lines.append(f"\nTotal: {len(all_files)} file(s)\n")

    mf = out_path / "chat-manifest.md"
    mf.write_text("\n".join(lines))
    print(f"  chat-manifest.md ({len(all_files)} files)")


def _cmd_all(config: dict, args, project_name: str, out_path: Path):
    clean_manifest(out_path, "")
    all_created = []
    for name in _list_profiles(config):
        try:
            profile = get_profile(name)
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)
        if args.compress:
            profile["compress"] = True
        if args.format:
            profile["section_format"] = args.format
        print(f"[{name}] Collecting...")
        created = collect(
            profile,
            project_name,
            str(out_path),
            verbose=args.verbose,
            incremental=args.incremental,
        )
        if created:
            all_created.extend(created)
            for f in created:
                _print_result(f)
        else:
            print("  No content collected.")

    # Write manifest
    _write_manifest(out_path, all_created, config)
    all_created.append("chat-manifest.md")

    save_manifest(out_path, all_created)


def _cmd_single(config: dict, args, project_name: str, out_path: Path):
    try:
        profile = get_profile(args.profile)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)
        return

    if args.compress:
        profile["compress"] = True
    if args.format:
        profile["section_format"] = args.format

    name_tmpl = profile.get("name_template", f"chat-{args.profile}")
    clean_manifest(out_path, name_tmpl)

    print(f"[{args.profile}] Collecting...")
    created = collect(
        profile,
        project_name,
        str(out_path),
        verbose=args.verbose,
        incremental=args.incremental,
    )

    prev = load_manifest(out_path)
    updated = [f for f in prev if not f.startswith(name_tmpl)]
    updated.extend(created)
    save_manifest(out_path, updated)

    if created:
        for f in created:
            _print_result(f)
    else:
        print("  No content collected.")


if __name__ == "__main__":
    main()
